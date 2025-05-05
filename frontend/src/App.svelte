<script>
  let userInput = "";
  let responseText = "";
  let isLoading = false;

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
        placeholder="Ask something..." 
        on:keydown={handleKeyPress}
        disabled={isLoading}
      ></textarea>
      <button on:click={sendQuery} disabled={isLoading || !userInput}>
        {isLoading ? 'Sending...' : 'Send'}
      </button>
    </div>
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
    min-height: 300px;
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
  }
  
  textarea {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    resize: vertical;
    min-height: 60px;
    font-family: inherit;
  }
  
  button {
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0 1.5rem;
    cursor: pointer;
    font-weight: bold;
    align-self: flex-end;
    height: 40px;
  }
  
  button:hover {
    background-color: #e63600;
  }
  
  button:disabled {
    background-color: #ffae99;
    cursor: not-allowed;
  }
</style>
