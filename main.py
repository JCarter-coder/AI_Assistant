# AI Assistant 
# Import libraries from CLI =>
# pip install tkinter tkmacosx llama-cpp-python pypdf

# Create a LLM with local GGUF model
#import llm_model
from llama_cpp import Llama
# Import PDF extraction library
from pypdf import PdfReader

# Implement a simple GUI
import tkinter as tk
from tkinter import scrolledtext, filedialog
# Time library for the timer
import time
# Threading for background tasks
import threading, multiprocessing
# Import better buttons for macOS
from tkmacosx import Button
# Use tooltips on buttons if needed
from helper import ToolTip

# Determine the number of CPU cores available on the system
num_cores = multiprocessing.cpu_count()
# Set the number of threads for the LLM, leaving 2 cores free
llm_threads = max(1, num_cores - 2)

# Initialize the Llama model
# This is important because we only want to load the model once
llm = Llama(
    # Let's set the path the model we want to use
    model_path="Dolphin3.0-Llama3.1-8B_Q5_K_M_T.gguf",
    # Set the context window size (i.e. how many tokens the model can "see" at once)
    # This includes the prompt and the response
    n_ctx=2048,
    # Set the number of threads to use for inference
    # I am setting it to 7 here, but you can adjust it based on your CPU
    n_threads=llm_threads,
    # Use GPU if avialable
    n_gpu_layers=-1,
    # Halve the KV cache size (from 32 to 16bit precision) for faster performance
    f16_kv=True,
    # Let us and the user know what is going on via console
    verbose=True,
)

# Global variables --------------------------------------
# Set a default font for the GUI
DEFAULT_FONT = ("Helvetica", 22)
# To track total tokens used
total_tokens_used = 0

# A flag to track if our model is generating a response
is_generating = False

# A string to hold uploaded PDF text
reader_text = ""

# Definitions -------------------------------------------

# Timer function to update elapsed time in GUI
def update_timer(start_time):
    # Let's loop until the model is done generating
    while is_generating:
        # Let's calculate the elapsed time
        elapsed_time = time.time() - start_time
        # Update a timer label in the GUI
        root.after(0, timer_label.config, {'text': f"Response time: {elapsed_time:.2f} seconds"})
        # Sleep for a short amount of time so our timer doesn't use too much CPU
        time.sleep(0.1)

def extract_text_from_pdf():
    global reader_text
    file_path = filedialog.askopenfilename(
        title="Select PDF file",
        filetypes=[("PDF Files", "*.pdf")]
    )

    # If no file was selected, return
    if not file_path:
        return
    else:
        try:
            # Read the PDF file object
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                # Extract text from each page
                text += page.extract_text() + "\n"
            reader_text = text
            # Disable button once a document has been loaded
            upload_button.config(state=tk.DISABLED,text="Uploaded")
            # Show message in console
            print(f"[PDF] Extracted {len(text)} characters from {file_path}")
        except Exception as e:
            print(f"[PDF Error] Could not extract text from {file_path}: {e}")

# Create a function to send the prompt to the model and get the response
def send_message():
    global reader_text
    global is_generating
    # Check if the model is already generating a response
    # if it is, then ignore this new request
    if is_generating:
        # When you return it exits the function early
        return
    
    # Get the text from the uploaded PDF
    if reader_text:
        pdf_text = reader_text
        # Clear the reader_text after using it
        reader_text = ""
        # Prepend the PDF text to the user's prompt
        entry.insert(0, f"PDF document:\n{pdf_text}\n\n")

    # Get the user's prompt from the input box
    user_input = entry.get()
    # Don't send empty prompts
    if not user_input.strip():
        return
    
    # Clear the input box
    entry.delete(0, tk.END)

    # Let's add a user message to our output box
    chat_display.insert(tk.END, user_input + "\n", "user")

    # Define a personal assistant for the model
    persona = (
        '''
            You are an advanced AI assistant named Ada.
            Engage in a helpful and thoughtful manner.
            \n\n
        '''    
    )

    full_prompt = persona + user_input

    # Let's disable the send button and entry box while we
    # wait for a response
    entry.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED, text="Sent")
    # Let our user know the model is processing the request
    timer_label.config(text="Thinking...")

    # IMPORTANT Multi-threading
    # Create and start the main background thread to handle
    # the model response so the GUI does not freeze
    threading.Thread(target=generate_response_threaded, args=(full_prompt,), daemon=True).start()
    # END of the send message function

# Create a function to handle the model response in a separate thread
def generate_response_threaded(full_prompt):
    # Let's hack this with a global var to modify our is_generating flag
    global is_generating
    # Set the flag to True to indicate the LLM is currently generating
    is_generating = True

    # Start the timer
    start_time = time.time()
    # IMPORTANT Multi-threading
    # We are making a timer update thread to keep our GUI responsive
    threading.Thread(target=update_timer, args=(start_time,), daemon=True).start()
    
    try:
        # Temporarily insert "Thinking..." on new line
        chat_display.insert(tk.END, f"\nThinking...", "bot")

        # Now let's get the model's response
        # THIS IS IMPORTANT
        # This is sent to the model each time the user hits send
        response = llm(
            f"User: {full_prompt}\nAssistant:",
            # We limit the response to 1024 tokens
            # This size does not include the prompt tokens size
            max_tokens=1024,
            # This will stop the model from generating more text and going on and on
            stop=["\nUser:", "\n\nUser:", "User:"],
            # We do not want our own prompt back in the response
            echo=False
        )

        # Now that we have the response we can set our flag to False
        is_generating = False

        # Let's extract the response text from the response object
        response_text = response['choices'][0]['text'].strip()

        # Calculate the total time taken for the response
        final_time = time.time() - start_time

        # Remove the last line, i.e. temporary "Thinking..." statement
        chat_display.delete("end-1c linestart", "end-1c lineend")

        # Now we need to update the GUI with the response and final time
        root.after(0, update_gui, response_text, final_time)
    
    except Exception as e:
        print("[LLM error]:", repr(e))
        root.after(0, update_gui, f"(Error: {e})", 0.0)

    finally:
        # Ensure the is_generating flag is reset in case of error
        is_generating = False

    # END of the function

# Create a function to update the GUI after the response is done
def update_gui(response_text, final_time):
    try:
        #global is_tts_speaking
        chat_display.insert(tk.END, f"({final_time:.2f} seconds)\n", "bot")
        # Add the model's response to our output box
        chat_display.insert(tk.END, f"{response_text}\n\n", "bot")
        # Let's auto scroll to the bottom of the chat display
        chat_display.see(tk.END)

        # Set the final time taken for the response on our timer label
        timer_label.config(text=f"Response time: {final_time:.2f} seconds")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Re-enable the upload, entry box, and send button
        upload_button.config(state=tk.NORMAL, text="Upload")
        entry.config(state=tk.NORMAL)
        send_button.config(state=tk.NORMAL, text="Send")

# Create a function to handle closing our app gracefully
def on_closing():
    # Clean up any resources if needed
    root.destroy()

# GUI Setup ---------------------------------------------

# Create our main window
root = tk.Tk()

# Set the title of the window
root.title("Local AI Assistant")

# Set the size of the window
root.geometry("1500x900")

# Configure grid layout of the main window
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=0)

# Create left and right containers for widgets
left_frame = tk.Frame(root, width=300, bg="gray10")
left_frame.grid(row=0, column=0, sticky="nesw")
left_frame.grid_propagate(False)
tk.Label(left_frame, text="Chat History", fg="white", font=DEFAULT_FONT).pack(anchor="center")

right_frame = tk.Frame(root, width=1200, bg="gray12")
right_frame.grid(row=0, column=1, sticky="nesw")

# Text Display Area ------------------------------------
# Text column for responses
right_frame.columnconfigure(0, weight=1)
# Scrollbar column
right_frame.columnconfigure(1, weight=0)
# Make the text column expandable
right_frame.rowconfigure(0, weight=1)

# Close and reset chat buttons area
form_controls = tk.Frame(root, width=300, height=50, bg="gray15")
form_controls.grid(row=1, column=0, padx=5, sticky="nesw")

form_controls.columnconfigure(0, weight=0)
form_controls.columnconfigure(1, weight=0)

# Entry area for user input/upload
entry_frame = tk.Frame(root, width=1200, height=50, bg="gray20")
entry_frame.grid(row=1, column=1, padx=5, sticky="nesw")

entry_frame.columnconfigure(0, weight=0)
entry_frame.columnconfigure(1, weight=1)
entry_frame.columnconfigure(2, weight=0)

# Interactive Area -------------------------------------

# Create a scrolled text box to display the widget
chat_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=20, font=DEFAULT_FONT)
# We want to span all three columns
chat_display.grid(row=0, column=0, padx=10, pady=10, stick="nesw")
# Make the chat display read-only
chat_display.config(state=tk.NORMAL)
# Tags for text alignment
chat_display.tag_configure("bot",
                           lmargin1=50, lmargin2=50, rmargin=500,
                           spacing1=4, spacing3=4)
chat_display.tag_configure("user", 
                           lmargin1=500, lmargin2=500, rmargin=50,
                           spacing1=4, spacing3=4)

# Buttons and Input Area ---------------------------------

# GUI application close button
close_button = Button(form_controls, text="Close", font=DEFAULT_FONT, command=on_closing)
close_button.grid(row=0, column=0, padx=5, pady=10, sticky="nesw")

# FIXME: Add new chat button functionality here when a database is linked
new_chat_button = Button(form_controls, text="New Chat", font=DEFAULT_FONT)
new_chat_button.grid(row=0, column=1, padx=5, pady=10, sticky="nesw")
# Let user know chat history will be implemented in future feature
ToolTip(new_chat_button, "Will be used with implentation of chat history")

# Upload button for .pdf document text extraction
upload_button = Button(entry_frame, text="Upload", font=DEFAULT_FONT, command=extract_text_from_pdf)
upload_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
# Let user know only .pdf files can be uploaded (at this time)
ToolTip(upload_button, "Upload a .pdf document for text extraction")

# Create an entry box for the user to type their prompt
entry = tk.Entry(entry_frame, font=DEFAULT_FONT)
# Place it in the grid at the first column of the second row
entry.grid(row=0, column=1, padx=(10,5), pady=10, sticky="ew")

# Create a send button
send_button = Button(entry_frame, text="Send", font=DEFAULT_FONT, command=send_message)
send_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")


# Create a label to display the timer
timer_label = tk.Label(root, text="Response time: 0.00 seconds", font=DEFAULT_FONT)
#timer_label.grid(row=3, column=0, columnspan=3, pady=(0,10), sticky="w")

# Bind the Enter key to the send_message function
root.bind('<Return>', lambda e: send_message())

# Check if the user closes the window with the X button
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main event loop - This will not run without this line!!
root.mainloop()

# Clean any leftover resources if needed...
print("Cleaning up resources and exiting")
del llm
print("Cleaning of LLM object complete. Goodbye!")