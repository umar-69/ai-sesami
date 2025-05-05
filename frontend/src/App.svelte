<script>
  import { onMount, onDestroy } from 'svelte';

  let userInput = "";
  let responseText = "";
  let isLoading = false;
  let status = 'Idle';
  let idToken = null;
  let ws = null;
  let character = 'Miles'; // Or 'Maya'
  const websocketUrlBase = 'wss://sesameai.app/agent-service-0/v1/connect';

  // --- New Audio State ---
  let isRecording = false;
  let audioContext = null;
  let mediaRecorder = null;
  let audioStream = null; // Store the stream to stop tracks later
  let receivedAudioQueue = []; // Queue for incoming audio buffers
  let isPlaying = false;      // Prevent overlapping playback
  let audioMimeType = 'audio/webm;codecs=opus'; // Common format, might need adjustment
  let audioTimeslice = 100; // Send data every 100ms

  async function sendQuery() {
    if (!userInput) return;
    
    isLoading = true;
    try {
      // Send the input to our backend API endpoint
      const res = await fetch("/api/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userInput })
      });
      
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      responseText = data.reply || "No response from AI";
    } catch (error) {
      console.error("Error calling API:", error);
      responseText = `Error: ${error.message}`;
    } finally {
      isLoading = false;
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendQuery();
    }
  }

  async function connectToSesame() {
    if (ws) {
      ws.close();
      ws = null;
    }
    status = 'Fetching token...';
    idToken = null;
    stopAudioPlaybackAndClearQueue(); // Clear any previous audio
    closeMediaRecorderAndStream(); // Ensure mic is released

    try {
      const response = await fetch('/api/voice'); // Assumes running via `vercel dev` or deployed
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to fetch token: ${response.status} ${errorData.error || ''}`);
      }
      const data = await response.json();
      idToken = data.id_token;
      status = 'Token received. Connecting WebSocket...';

      if (!idToken) {
        throw new Error('Received null or empty token from API.');
      }

      // Construct the full WebSocket URL
      const fullWsUrl = `${websocketUrlBase}?character=${character}&token=${idToken}`;
      console.log('Attempting WebSocket connection to:', fullWsUrl); // Log the URL

      // --- WebSocket Connection ---
      ws = new WebSocket(fullWsUrl);

      ws.onopen = () => {
        status = 'WebSocket Connected! Hold button to talk.';
        console.log('WebSocket connection established.');
        ws.binaryType = 'arraybuffer'; // <<< IMPORTANT: Expect binary audio data
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          console.log(`Received ${event.data.byteLength} bytes of audio data.`);
          status = 'Receiving audio...';
          receivedAudioQueue.push(event.data); // Add chunk to queue
          playNextAudioChunk(); // Attempt to play if not already playing
        } else {
          // Handle potential text messages if the API sends them
          console.log('WebSocket text message received:', event.data);
          status = `Received Text: ${event.data}`;
        }
      };

      ws.onerror = (error) => {
        // Correctly handle potential error event types
        const errorMessage = error instanceof ErrorEvent ? error.message : 'Unknown WebSocket error';
        status = `WebSocket Error: ${errorMessage}`;
        console.error('WebSocket error:', error); // Log the full event for details
        ws = null;
      };

      ws.onclose = (event) => {
        if (event.wasClean) {
          status = `WebSocket Closed (Code: ${event.code}) - Reconnect if needed.`;
          console.log(`WebSocket closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
          // e.g. server process killed or network down
          status = `WebSocket Connection Died (Code: ${event.code}) - Reconnect if needed.`;
          console.error('WebSocket connection died');
        }
        ws = null;
        idToken = null;
        stopAudioPlaybackAndClearQueue();
        closeMediaRecorderAndStream();
      };

    } catch (error) {
      status = `Error: ${error.message}`;
      console.error('Connection process error:', error);
      ws = null; // Ensure ws is null on error
      idToken = null;
    }
  }

  // --- Audio Playback --- 
  function getAudioContext() {
    if (!audioContext) {
      // Rely on the standard AudioContext
      if (window.AudioContext) {
         audioContext = new window.AudioContext();
         console.log('AudioContext created.');
      } else {
         console.error('Web Audio API (AudioContext) not supported on this browser.');
         status = 'Error: AudioContext not supported.';
         // Return null or handle the absence appropriately
         return null; 
      }
    }
    return audioContext;
  }

  async function playNextAudioChunk() {
    if (isPlaying || receivedAudioQueue.length === 0) {
      return; // Don't play if already playing or queue empty
    }

    isPlaying = true;
    const audioData = receivedAudioQueue.shift(); // Get the next chunk
    const localAudioContext = getAudioContext();

    if (!localAudioContext) {
      console.error('AudioContext not available.');
      status = 'Error: AudioContext not available.';
      isPlaying = false;
      return;
    }

    try {
      status = 'Decoding & Playing audio...';
      const audioBuffer = await localAudioContext.decodeAudioData(audioData);
      const source = localAudioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(localAudioContext.destination);
      source.onended = () => {
        console.log('Audio chunk finished playing.');
        status = 'Playback finished. Ready for next chunk or talk.';
        isPlaying = false;
        playNextAudioChunk(); // Check if more chunks arrived while playing
      };
      source.start(0); // Play immediately
      console.log('Starting playback of audio chunk.');
    } catch (error) {
      console.error('Error decoding or playing audio data:', error);
      status = `Audio Playback Error: ${error.message}`;
      isPlaying = false;
      // Maybe try next chunk even if this one failed?
      playNextAudioChunk(); 
    }
  }
  
  function stopAudioPlaybackAndClearQueue() {
     // Basic approach: just clear queue. More robust would be to stop current source node.
     receivedAudioQueue = [];
     isPlaying = false;
     console.log('Audio queue cleared.');
     // If audioContext exists and a source node is active, you might want to stop it:
     // Find a way to track the current source node and call source.stop()
  }

  // --- Microphone Recording --- 
  async function startRecording() {
    if (isRecording || !ws || ws.readyState !== WebSocket.OPEN) {
      console.log('Cannot start recording: Already recording, WebSocket not connected, or button disabled.');
      status = ws && ws.readyState === WebSocket.OPEN ? status : 'Connect WebSocket first!';
      return;
    }

    status = 'Requesting Mic...';
    try {
      // Ensure AudioContext is ready for potential later use
      getAudioContext(); 
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         throw new Error('getUserMedia not supported on your browser!');
      }

      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      status = 'Mic Access Granted. Recording...';
      isRecording = true;
      console.log('Microphone access granted.');

      mediaRecorder = new MediaRecorder(audioStream, { mimeType: audioMimeType });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
          console.log(`Sending ${event.data.size} bytes of audio data.`);
          ws.send(event.data); // Send Blob directly
        } else {
          if (!ws || ws.readyState !== WebSocket.OPEN) {
             console.warn('WebSocket closed or not open while trying to send audio.');
             // Consider stopping recording if WS closes unexpectedly mid-recording
             // stopRecording(); 
          }
        }
      };

      mediaRecorder.onstop = () => {
        console.log('MediaRecorder stopped.');
        status = 'Recording stopped. Processing...';
        // The actual 'processing' happens as the chunks are received by the server
        // and response comes back via ws.onmessage
      };
       mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder Error:', event.error);
        status = `Recorder Error: ${event.error.name}`;
        stopRecording(); // Stop recording on error
      };

      mediaRecorder.start(audioTimeslice); // Start recording, slicing into chunks
      console.log('MediaRecorder started.');

    } catch (error) {
      console.error('Error starting recording:', error);
      status = `Mic/Recording Error: ${error.message}`;
      isRecording = false;
      closeMediaRecorderAndStream(); // Clean up
    }
  }

  function stopRecording() {
    if (!isRecording || !mediaRecorder) {
      // console.log('Not recording or recorder not initialized.');
      return;
    }
    
    console.log('Attempting to stop recording...');
    if (mediaRecorder.state === 'recording') {
       mediaRecorder.stop();
    }
    isRecording = false;
    // Stream tracks are stopped in closeMediaRecorderAndStream
    closeMediaRecorderAndStream(); 
    // Don't reset status here, let onstop or playback handle it
  }

  function closeMediaRecorderAndStream() {
     if (mediaRecorder && mediaRecorder.state !== 'inactive') {
       try { mediaRecorder.stop(); } catch(e) { console.warn('Error stopping media recorder:', e);}
     }
     if (audioStream) {
       audioStream.getTracks().forEach(track => track.stop());
       console.log('Audio stream tracks stopped.');
     }
     mediaRecorder = null;
     audioStream = null;
     isRecording = false; // Ensure state is reset
  }

  // Cleanup WebSocket on component destroy
  onMount(() => {
    // Check for MediaRecorder support
    if (!window.MediaRecorder) {
        status = 'Error: MediaRecorder API not supported on this browser.';
        console.error('MediaRecorder API not supported.');
    }
    // Check for AudioContext support
    if (!window.AudioContext) { // Simplified check
        status = 'Error: Web Audio API not supported on this browser.';
        console.error('Web Audio API not supported.');
    }
    
    // Add listeners to stop recording if mouse leaves button while pressed
    const talkButton = document.getElementById('talk-button');
    if (talkButton) {
       talkButton.addEventListener('mouseleave', stopRecording);
    }

    return () => {
      // Component cleanup (inherited from previous version)
      if (ws) {
        console.log('Closing WebSocket connection on component destroy.');
        ws.close();
      }
      closeMediaRecorderAndStream();
      if (audioContext && audioContext.state !== 'closed') {
          audioContext.close();
          console.log('AudioContext closed.');
      }
      // Remove listener
       if (talkButton) {
         talkButton.removeEventListener('mouseleave', stopRecording);
       }
    };
  });

  // Use onDestroy for final cleanup if onMount return isn't sufficient (usually is)
  // onDestroy(() => { ... });
</script>

<main>
  <div class="container">
    <h1>Sesame AI Voice Chat</h1>
    
    <div class="chat-container">
      {#if responseText}
        <div class="response-container">
          <p class="response-text">{responseText}</p>
        </div>
      {/if}
    </div>
    
    <div class="input-container">
      <textarea 
        bind:value={userInput} 
        placeholder="Ask something... (Optional Text Input)" 
        on:keydown={handleKeyPress}
        disabled={isLoading}
      ></textarea>
      <button on:click={sendQuery} disabled={isLoading || !userInput}>
        {isLoading ? 'Sending...' : 'Send Text'}
      </button>
    </div>

    <div class="voice-controls">
      <button on:click={connectToSesame} disabled={status.includes('Connecting') || status.includes('Fetching') || !!ws}>
         {ws ? 'Reconnect' : 'Connect'} to Sesame AI ({character})
      </button>
      {#if ws}
        <button 
          id="talk-button" 
          on:mousedown={startRecording} 
          on:mouseup={stopRecording}
          class:recording={isRecording}
          disabled={!ws || ws.readyState !== WebSocket.OPEN || status.includes('Error')} 
        >
           {isRecording ? 'Recording...' : 'Hold to Talk'}
        </button>
      {/if}
    </div>

    <p>Status: {status}</p>

    {#if idToken}
      <p>ID Token: <small>{idToken.substring(0, 30)}...</small></p>
    {/if}

  </div>
</main>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    font-family: Arial, sans-serif;
  }
  
  h1 {
    color: #ff3e00;
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .chat-container {
    min-height: 100px; /* Reduced height as focus is voice */
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    overflow-y: auto;
  }
  
  .response-container {
    background-color: #fff;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
  }
  
  .response-text {
    margin: 0;
    line-height: 1.5;
  }
  
  .input-container {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem; /* Add space below text input */
  }
  
  textarea {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    resize: vertical;
    min-height: 40px; /* Smaller default height */
    font-family: inherit;
  }
  
  button {
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.5em 1.5em; /* Adjusted padding */
    cursor: pointer;
    font-weight: bold;
    height: 40px; /* Consistent height */
    white-space: nowrap; /* Prevent button text wrapping */
  }
  
  button:hover {
    background-color: #e63600;
  }
  
  button:disabled {
    background-color: #ffae99;
    cursor: not-allowed;
  }
  
  .voice-controls {
      display: flex;
      gap: 1rem;
      margin-bottom: 1rem;
      align-items: center;
  }
  
  #talk-button.recording {
      background-color: #c00; /* Indicate recording state */
  }

  small {
    word-break: break-all;
  }
</style>
