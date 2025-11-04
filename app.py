import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
import time

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Chatbot")
    
# Add a setup section
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

def complete_setup():
    st.session_state.setup_complete = True

def complete_chat():
    st.session_state.chat_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

def clear_session_state():
    for key in st.session_state.keys():
        del st.session_state[key]

# display the setup form only if not complete
if not st.session_state.setup_complete:
    st.subheader("Personal Information", divider='rainbow')

    if "name" not in st.session_state:
        st.session_state.name = ""
    if "experience" not in st.session_state:
        st.session_state.experience = ""
    if "skills" not in st.session_state:
        st.session_state.skills = ""

    st.session_state.name = st.text_input("Name:", max_chars=40, placeholder="Enter your name here...")
    st.session_state.experience = st.text_area("Experience:", value="", max_chars=200, placeholder="Describe your experience here...")
    st.session_state.skills = st.text_area("Skills:", value="", max_chars=200, placeholder="List your skills here...")

    # test if info is captured 
    # st.write(f"**Your Name:** {st.session_state.name}")
    # st.write(f"**Your Experience:** {st.session_state.experience}")
    # st.write(f"**Your Skills:** {st.session_state.skills}")

    st.subheader("Company and Positions", divider='rainbow')

    if "level" not in st.session_state:
        st.session_state.level = "Junior"
    if "position" not in st.session_state:
        st.session_state.position = "Software Engineer"
    if "company" not in st.session_state:
        st.session_state.company = "Google"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio("Select your level:",key="visibility", options= ["Junior", "Mid-level", "Senior"])

    with col2:
        st.session_state.position = st.selectbox("Select your desired position:", options=["Software Engineer", "Data Scientist", "Product Manager", "Designer", "ML Engineer", "BI Analyst", "Financial Analyst"])

    st.session_state.company = st.selectbox("Select the company you are applying to:", options=["Google", "Microsoft", "Apple", "Amazon", "Facebook", "Netflix", "Tesla", "Udemy", "Spotify", "Airbnb"])

    # test if info is captured 
    # st.write(f"**Your information:** {st.session_state.level} {st.session_state.position} at {st.session_state.company}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete! Starting interview...")

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """ 
        Start by introducing yourself
        """,
        icon="🙌"
    )

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"

    if not st.session_state.messages:
        st.session_state.messages = [{'role': 'system', 
                                      'content': f"Your name is Sofia and you are an HR executive that interviews candidates for tech positions. \
                                        You will interview an interviewee called {st.session_state.name} \
                                        with experience {st.session_state.experience} and skills {st.session_state.skills}. \
                                        The interviewee is applying for the position of {st.session_state.level} {st.session_state.position} at company {st.session_state.company}. \
                                        Conduct a friendly and professional interview, asking relevant questions about their background, skills, and suitability for the role. Provide feedback and next steps at the end of the interview."
                                    }]

    # Display historic messages
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Type your message here...", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=st.session_state.messages,
                        stream=True
                    )
                    response = st.write_stream(stream)      # the response is based on last user prompt

                st.session_state.messages.append({"role": "assistant", "content": response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        complete_chat()
        st.success("The interview is complete. Thank you for your time!", icon="✅")

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Interview Feedback", divider='rainbow')

    conversation_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages if m['role'] != 'system'])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_system_prompt = """You are an expert HR professional providing interview feedback. 
        Before the feedback, give a score of 1 to 10. 
        Follow this format: 
        Overall Score: X/10 // your score here
        Feedback: // your detailed feedback here
        Give only the feedback without any additional questions.
        """
    
    feedback_user_prompt = f"""Based on the following interview conversation, provide detailed feedback for {st.session_state.name} who applied for the position of {st.session_state.level} {st.session_state.position} at {st.session_state.company}.
        Highlight strengths, areas for improvement, and overall suitability for the role. Do not engage in conversation.
        Interview Conversation: {conversation_history}
        """

    feedback_completion = feedback_client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=[
            {'role': 'system', 'content': feedback_system_prompt},
            {'role': 'user', 'content': feedback_user_prompt}
        ],
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("Restart Interview"):  # having type seems to break the button
        # streamlit_js_eval(js_expression="window.location.reload()")       // couldnt get this working

        # manually clearing the session state and use streamlit rerun seems to work
        clear_session_state()
        st.rerun()
        