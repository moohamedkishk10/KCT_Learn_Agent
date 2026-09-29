import nest_asyncio
nest_asyncio.apply()

import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest 

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate  
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.exceptions import LangChainException

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__) 

llm = None
prompt_template = None

if GEMINI_API_KEY:
    try:
        llm = GoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=GEMINI_API_KEY
        )

        template = """
        You are KCT Learn Agent, a Structured Personal Instructor, Code Grader, and Academic Mentor. You possess vast, multi-year working experience as a senior engineer and researcher at top-tier global tech companies like Google, Microsoft, and others, specializing in both Artificial Intelligence (AI) and Data Science. Your primary role is to guide the user through a complex subject or career roadmap (AI or Data Science) from the absolute beginning to an expert level, focusing heavily on practical application and code quality.

        Language and Dialect Rule: You are fluent in all languages and dialects. Always communicate using the user's chosen language or dialect for maximum comfort and clarity.

        Your process MUST follow these phases sequentially:
        
        PHASE 1: Initialization & Curriculum Design
        1. First Turn Only (Initialization): If the user hasn't specified a track, your FIRST response must be to ask: "Which track would you like to master today: Artificial Intelligence (AI) or Data Science?"
        2. Roadmap Generation: Once the user specifies the track, you must propose a detailed, numbered, multi-module curriculum (roadmap) that covers the track completely from level 0 to Expert.

        PHASE 2: Deep Instruction, Mastery, and Pacing (Ongoing)
        1. Start: Present only the content for the current step/module.
        2. Goal: Your goal is to ensure the user achieves an Expert Level of understanding and competence in this specific module before moving on.
        3. Explain: Provide a clear, detailed, and comprehensive explanation.
        4. Dual Assessment: Conclude the response by presenting two mandatory tasks:
           a. Theoretical Question: A direct question to confirm understanding.
           b. Practical Task: A request to write specific code to solve a problem related to the material taught.
        5. Wait: NEVER proceed to the next step or topic until the user has successfully passed both the theoretical and practical tasks.
        
        PHASE 3: Code Grading and Feedback (Whenever code is received)
        If the user submits code, immediately shift your role to Code Reviewer/Grader:
        * Correction & Review: Analyze the code for correctness, efficiency, and best practices.
        * Feedback: Provide detailed, constructive feedback.
        * Approval: Grant approval only if the code is correct and the theoretical question is answered satisfactorily.

        PHASE 4: Next Step Transition & Final Project
        * Transition: When the user successfully completes both checks, introduce the title and content for the next sequential step.
        * Final Project (Last Step): The very last step of the roadmap must be: "Final Capstone Project" where the user applies all learned skills to build a complete project.

        Rules for Response:
        * Format: Use clear headings, bullet points, and code blocks for examples.
        * Language: Respond in the user's chosen language or dialect.

        Conversation History:
        {history}
        
        Human Input: {input}
        Instructor/Grader:
        """

        prompt_template = PromptTemplate(
            input_variables=["history", "input"],
            template=template
        )
    except Exception as e:
        logger.error(f"Error initializing Gemini model: {e}")
        llm = None


def get_conversation_chain(update: Update, context: ContextTypes.DEFAULT_TYPE, llm_instance, prompt_instance):
    """Retrieve or create a unique conversation chain with memory per user."""
    user_id = update.effective_user.id 
    
    if user_id not in context.user_data:
        logger.info(f"Creating new conversation chain for user: {user_id}")
        
        new_memory = ConversationBufferMemory(
            ai_prefix="Instructor/Grader",
            human_prefix="Human Input",
            memory_key="history"
        )
        new_chain = ConversationChain(
            llm=llm_instance, 
            memory=new_memory, 
            prompt=prompt_instance,
            verbose=False 
        )
        context.user_data[user_id] = new_chain
        
    return context.user_data[user_id]


async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Split and send long messages as plain text."""
    MAX_CHARS = 4096
    
    for i in range(0, len(text), MAX_CHARS):
        chunk = text[i:i + MAX_CHARS]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=chunk,
            parse_mode=None
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond to /start command with a welcome message."""
    welcome_message = (
        "Welcome to KCT Learn Agent! I am your Professor Assistant.\n"
        "I'm ready to help you with any academic question you have.\n\n"
        "Which track would you like to master today: Artificial Intelligence (AI) or Data Science?"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message,
        parse_mode=None
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user messages and send them to the LLM model."""
    if not llm:
        await update.message.reply_text(
            "Sorry, I cannot respond. There is an issue with model setup (Gemini API). Please check your .env file."
        )
        return

    try:
        current_chain = get_conversation_chain(update, context, llm, prompt_template)
    except Exception as e:
        logger.error(f"Error retrieving/creating conversation chain: {e}")
        await update.message.reply_text("Sorry, an error occurred while initializing your session memory.")
        return

    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = current_chain.invoke({"input": user_message})
        
        if isinstance(response, dict) and 'response' in response:
            ai_response = response['response']
        elif isinstance(response, str):
            ai_response = response
        else:
            ai_response = "Sorry, encountered an issue parsing the response from the model."
        
        await send_long_message(update, context, ai_response)

    except BadRequest as e:
        logger.error(f"Telegram error: {e}.")
        await update.message.reply_text("Sorry, an error occurred while formatting the response.")
    except LangChainException as e:
        logger.error(f"LangChain/Gemini error: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request (temporary issue connecting to Gemini model)."
        )
    except Exception as e:
        error_message = str(e)
        if "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
            logger.error(f"Rate limit exceeded (Quota): {e}")
            response_text = "Sorry, the usage limit for Gemini free tier has been exceeded. Please try again later."
        else:
            logger.error(f"General error: {e}")
            response_text = "Sorry, an unexpected error occurred. Please try again."
            
        await update.message.reply_text(response_text)


def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Error: Please ensure TELEGRAM_TOKEN and GEMINI_API_KEY are set in the .env file.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("KCT Learn Agent is now running and ready to respond using Gemini 2.5 Flash and individual user memory. Do not close this window.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()