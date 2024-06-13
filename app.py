from datetime import datetime,timedelta
import logging
import boto3
import json
import streamlit as st
import os
from streamlit_cognito_auth import CognitoAuthenticator
from utils import clear_input, show_empty_container, show_footer
from connections import Connections
from dotenv import load_dotenv
import requests
load_dotenv()
secrets_manager = boto3.client('secretsmanager',os.environ['AWS_REGION'])  
def retrieve_secrets(secret_names):  
    secrets = {}  
    for secret_name in secret_names:  
        try:  
            response = secrets_manager.get_secret_value(SecretId=secret_name)  
            secret_value = json.loads(response['SecretString'])  
            secrets[secret_name] = secret_value  
        except secrets_manager.exceptions.ResourceNotFoundException:  
            print(f"Secret {secret_name} not found.")  
      
    return secrets  

required_secret_names = ['COGNITO_USER_POOL_ID', 'COGNITO_APP_CLIENT_ID', 'COGNITO_APP_CLIENT_SECRET']  
retrieved_secrets = retrieve_secrets(required_secret_names)  

pool_id = retrieved_secrets.get('COGNITO_USER_POOL_ID')  
app_client_id  = retrieved_secrets.get('COGNITO_APP_CLIENT_ID')  
app_client_secret = retrieved_secrets.get('COGNITO_APP_CLIENT_SECRET')

st.set_page_config(
        page_title="SageMaker (Pricing) Chatbot", page_icon=":rock:", layout="centered"
    )
cookie_duration = timedelta(hours=0.5)
authenticator = CognitoAuthenticator(
    pool_id=pool_id,
    app_client_id=app_client_id,
    app_client_secret=app_client_secret,
    use_cookies=True,
)

is_logged_in = authenticator.login()
if not is_logged_in:
    st.stop()


def logout():
    print("Logout in example")
    authenticator.logout()


logger = logging.getLogger(__name__)
logger.setLevel(Connections.log_level)

# lambda_client = Connections.lambda_client


def get_response(user_input, session_id):
    """
    Get response from genai Lambda
    """
    api_url = 'https://bkmlztuk3m.execute-api.us-east-1.amazonaws.com/dev/chat/'
    logger.debug(f"session id: {session_id}")
    payload = {"body": json.dumps(
        {"query": user_input, "session_id": session_id})}

    # lambda_function_name = Connections.lambda_function_name

    # response = lambda_client.invoke(
    #     FunctionName=lambda_function_name,
    #     InvocationType="RequestResponse",
    #     Payload=json.dumps(payload),
    # )
    
    # response_output = json.loads(response["Payload"].read().decode("utf-8"))
    response = requests.post(api_url, json=payload)  
    response_output = response.json()  
    logger.debug(f"response_output from genai lambda: {response_output}")
    return response_output  


with st.sidebar:
    st.text(f"Welcome,\n{authenticator.get_username()}")
    st.header("Chat History")
    st.button("Logout", "logout_btn", on_click=logout)
def header():
    """
    App Header setting
    """
    # --- Set up the page ---
    
    st.image(
        "https://pypi-camo.global.ssl.fastly.net/a16d902540297868fece35aa6b6704677f07ad90/68747470733a2f2f6769746875622e636f6d2f6177732f736167656d616b65722d707974686f6e2d73646b2f7261772f6d61737465722f6272616e64696e672f69636f6e2f736167656d616b65722d62616e6e65722e706e67",
        width=250,
    )
    st.header("SageMaker (Pricing) Demo")
    st.write("Ask me about SageMaker, and SageMaker Pricing on training/inference")
    st.write("-----")


def initialization():
    """
    Initialize sesstion_state variablesß
    """
    # --- Initialize session_state ---
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(datetime.now()).replace(" ", "_")
        st.session_state.questions = []
        st.session_state.answers = []

    if "temp" not in st.session_state:
        st.session_state.temp = ""

    # Initialize cache in session state
    if "cache" not in st.session_state:
        st.session_state.cache = {}


def show_message():
    """
    Show user question and answers
    """

    # --- Start the session when there is user input ---
    user_input = st.text_input("# **Question:** 👇", "", key="input")
    # Start a new conversation
    new_conversation = st.button(
        "New Conversation", key="clear", on_click=clear_input)
    if new_conversation:
        st.session_state.session_id = str(datetime.now()).replace(" ", "_")
        st.session_state.user_input = ""

    if user_input:
        session_id = st.session_state.session_id
        with st.spinner("Gathering info ..."):
            vertical_space = show_empty_container()
            vertical_space.empty()
            output = get_response(user_input, session_id)
            logger.debug(f"Output: {output}")
            result = output["answer"]
            st.write("-------")
            source = output["source"]
            if source.startswith("SELECT"):
                source = f"_{source}_"
            # else:
            #     source = source.replace('\n', '\n\n')
            source_title = "\n\n **Source**:" + "\n\n" + source
            answer = "**Answer**: \n\n" + result
            st.session_state.questions.append(user_input)
            st.session_state.answers.append(answer + source_title)

    if st.session_state["answers"]:
        for i in range(len(st.session_state["answers"]) - 1, -1, -1):
            with st.chat_message(
                name="human",
                avatar="https://api.dicebear.com/7.x/notionists-neutral/svg?seed=Felix",
            ):
                st.markdown(st.session_state["questions"][i])

            with st.chat_message(
                name="ai",
                avatar="https://assets-global.website-files.com/62b1b25a5edaf66f5056b068/62d1345ba688202d5bfa6776_aws-sagemaker-eyecatch-e1614129391121.png",
            ):
                st.markdown(st.session_state["answers"][i])


# --- Section 1 ---
header()
# --- Section 2 ---
initialization()
# --- Section 3 ---
show_message()
# --- Foot Section ---
show_footer()


