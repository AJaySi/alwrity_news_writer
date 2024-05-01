import time #Iwish
import os
import json
import requests
import streamlit as st
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import google.generativeai as genai


def main():
    # Set page configuration
    st.set_page_config(
        page_title="Alwrity - AI News Reporter(Beta)",
        layout="wide",
    )
    # Remove the extra spaces from margin top.
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
        </style>
        """, unsafe_allow_html=True)
    st.markdown(f"""
      <style>
      [class="st-emotion-cache-7ym5gk ef3psqc12"]{{
            display: inline-block;
            padding: 5px 20px;
            background-color: #4681f4;
            color: #FBFFFF;
            width: 300px;
            height: 35px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            border-radius: 8px;’
      }}
      </style>
    """
    , unsafe_allow_html=True)

    # Hide top header line
    hide_decoration_bar_style = '<style>header {visibility: hidden;}</style>'
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    # Hide footer
    hide_streamlit_footer = '<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>'
    st.markdown(hide_streamlit_footer, unsafe_allow_html=True)

    # Title and description
    st.title("✍️ Alwrity - AI News Report Generator(Beta)")


    with st.expander("**PRO-TIP** - Read the instructions below.", expanded=True):
        news_keywords = st.text_input("Enter News Headlines to search Google News on:", 
                                      placeholder="News item to get latest results on..")
        col1, col2, space = st.columns([5, 5, 0.5])
        with col1:
            # Radio Buttons for Origin Country
            news_country = st.radio("Select origin country of the News event:",
                         options=["Spain", "Vietnam", "Pakistan", "India", "Germany", "China"],
                         index=3)
        with col2:
            # Radio Buttons for News Language
            news_language = st.radio("Select news article language to search for:",
                         options=["English", "Spanish", "Vietnamese", "Arabic", "Hindi", "German", "Chinese"],
                         index=0)
        
    # Generate Blog FAQ button
    if st.button('**Write News Report**'):
        if not news_keywords or len(news_keywords.split()) < 2:
            st.error("🚫 News keywords should be at least two words long. Least, you can do..")
        
        with st.status("Assigning the News to Virtual Reporter..", expanded=True) as status:
            st.write(f"Reading News articles on {news_keywords} from {news_country}..")
            news_report = perform_serper_news_search(news_keywords, news_country, news_language, status)
            print(news_report)
            # Clicking without providing data, really ?
            if news_report:
                status.update(label="Found some News aritcles, Creating News report..")
                final_report = write_news_google_search(news_keywords, news_country, news_language, news_report, status)
                st.subheader(f'**🧕🔬👩 Verify: Alwrity can make mistakes. Your Final News Report on {news_keywords}!**')
                st.write(final_report)
                status.update(label="Done: Scroll Down. Please Verify, Alwrity can make mistakes!", state="complete", expanded=True)
            else:
                st.write("💥**Failed to generate News Report. Please try again!**")


def write_news_google_search(news_keywords, news_country, news_language, search_results, status):
    """Combine the given online research and gpt blog content"""
    news_language = get_language_name(news_language)
    news_country = get_country_name(news_country)

    prompt = f"""
        As an experienced {news_language} news journalist and senior editor.
        I will provide you with my 'News keywords' and its 'Google News Results'.
        Your Task is to write a detailed {news_language} News report, from the given Google Nearch Results.
        Important, as a news report, its imperative that your content is factually correct and cited.
        
        Follow below guidelines:
        1). Understand and utilize the provided Google News Results.
        2). Always provide in-line citations and provide referance links.
        4). Always include the dates when then news was reported.
        6). Do not explain, describe your response.
        7). Your blog should be highly formatted in markdown style and in {news_language} language.
        8). Important: Please read the entire prompt before writing anything. Follow the prompt exactly as I instructed.

        \n\nNews Keywords: "{news_keywords}"\n\n
        Google News Result: "{search_results}"
        """
    status.update(label="Writing News report from Google News search results.")
    try:
        response = generate_text_with_exception_handling(prompt)
        return response
    except Exception as err:
        st.error(f"Exit: Failed to get response from LLM: {err}")
        exit(1)


def perform_serper_news_search(news_keywords, news_country, news_language, status):
    """ Function for Serper.dev News google search """
    # Get the Serper API key from environment variables
    news_language = get_language_name(news_language)
    news_country = get_country_name(news_country)

    status.update(label=f"Doing Google News Search, Wait for Breaking News.. {news_keywords} - {news_country} - {news_language}")
    serper_api_key = os.getenv('SERPER_API_KEY')

    # Check if the API key is available
    if not serper_api_key:
        raise ValueError("SERPER_API_KEY is missing. Set it in the .env file.")

    # Serper API endpoint URL
    url = "https://google.serper.dev/news"
    payload = json.dumps({
        "q": news_keywords,
        "gl": news_country,
        "hl": news_language
    })
    # Request headers with API key
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    # Send a POST request to the Serper API with progress bar
    with st.spinner("Doing Google News Search, Wait for Breaking News.."):
        response = requests.post(url, headers=headers, data=payload, stream=True)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse and return the JSON response
            #process_search_results(response, "news")
            return response.json()
        else:
            # Print an error message if the request fails
            st.error(f"Error: {response.status_code}, {response.text}")


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def generate_text_with_exception_handling(prompt):
    """
    Generates text using the Gemini model with exception handling.

    Args:
        api_key (str): Your Google Generative AI API key.
        prompt (str): The prompt for text generation.

    Returns:
        str: The generated text.
    """

    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
        }

        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]

        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)

        convo = model.start_chat(history=[])
        convo.send_message(prompt)
        return convo.last.text

    except Exception as e:
        st.exception(f"An unexpected error occurred: {e}")
        return None


def get_language_name(language_code):
    languages = {
            "Spanish": "es",
            "Vietnamese": "vn",
            "English": "en",
            "Arabic": "ar",
            "Hindi": "hi",
            "German": "de",
            "Chinese (Simplified)": "zh-cn"
        # Add more language codes and corresponding names as needed
    }
    return languages.get(language_code, "Unknown")


def get_country_name(country_code):
    countries = {
            "Spain": "es",
            "Vietnam": "vn",
            "Pakistan": "pk",
            "India": "in",
            "Germany": "de",
            "China": "cn"
        # Add more country codes and corresponding names as needed
        }
    return countries.get(country_code, "Unknown")


if __name__ == "__main__":
    main()
