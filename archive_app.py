import streamlit as st
from config import get_ai71_api_key
from audio import play_audio
from file_utils import extract_text_from_pdf as _extract_text_from_pdf, extract_text_from_word as _extract_text_from_word
from ai_utils import generate_response as _generate_response
from similarity import compare_summaries, rewrite_summary, identify_lacking_elements
from streamlit_navigation_bar import st_navbar

# Set the page configuration to wide layout
st.set_page_config(layout="wide")

# Define the tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Introduction", "Manual Resume Assistant", "Automatic Resume Builder", "Course Creator","Scoring Utility"])

# Display the Introduction
with tab1:
    st.write("""
            Welcome to the Resume Builder! This tool is designed to help you create professional and polished resumes quickly and easily.
            Follow the steps in this guide to get started and learn how to use all the features of the Resume Builder.
        """)
    st.title("Introduction to Resume Builder")
    st.image("images/falconSB.png")
    # st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Replace with your video URL

with tab2:
    AI71_API_KEY = get_ai71_api_key()
    
    st.title("AI71 Manual Resume Assistant")
    
    # Initialize session state variables
    session_vars = ['job_desc_text', 'resume_text', 'summaries', 'summary_response', 'job_roles', 'technical', 'history', 'educational', 'certification', 'cover', 'results']
    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = ""
    
    # Caching file extraction functions
    @st.cache_data
    def extract_text_from_pdf(file):
        return _extract_text_from_pdf(file)
    
    @st.cache_data
    def extract_text_from_word(file):
        return _extract_text_from_word(file)
    
    # Caching API call function
    @st.cache_data
    def generate_response(system_message, user_message):
        return _generate_response(system_message, user_message)
    
    st.subheader("Upload Job Description and Resume")
    
    with st.container():
        col1, col2 = st.columns(2)
    
        with col1:
            job_desc_file = st.file_uploader("Upload Job Description (PDF or Word)", type=["pdf", "docx", "doc"], key="job_desc_uploader")
            if job_desc_file is not None:
                if job_desc_file.type == "application/pdf":
                    st.session_state.job_desc_text = extract_text_from_pdf(job_desc_file)
                elif job_desc_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                    st.session_state.job_desc_text = extract_text_from_word(job_desc_file)
                st.text_area("Job Description Text", value=st.session_state.job_desc_text, height=200, key="job_description_text")
    
        with col2:
            resume_file = st.file_uploader("Upload Resume (PDF or Word)", type=["pdf", "docx", "doc"], key="resume_uploader")
            if resume_file is not None:
                if resume_file.type == "application/pdf":
                    st.session_state.resume_text = extract_text_from_pdf(resume_file)
                elif resume_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                    st.session_state.resume_text = extract_text_from_word(resume_file)
                st.text_area("Resume Text", value=st.session_state.resume_text, height=200, key="resume_text")
    
    st.subheader("Title Summary")
    
    with st.container():
        title_summary_col1, title_summary_col2 = st.columns([1, 1])
    
        with title_summary_col1:
            if 'ai_algorithm' not in st.session_state:
                st.session_state.ai_algorithm = """
    Produce 3 perfect synthetic career summaries for that job description based on the rules below, don't be verbose only 2 to 3 sentences.
    A career summary on a resume is a brief introduction that highlights your most significant achievements, skills, and experiences. It provides a snapshot of your professional background and showcases your qualifications in a concise manner. Here are some tips for writing an effective career summary:
    Keep It Concise
    Aim for a summary that is 2-3 sentences long. It should be a quick read that captures the essence of your career.
    Tailor It to the Job
    Customize your summary to match the specific job you are applying for. Highlight the skills and experiences most relevant to the position.
    Focus on Key Achievements
    Include your most notable accomplishments, especially those that demonstrate your ability to excel in the role you are targeting.
    Use Strong Action Words
    Start sentences with powerful action verbs to convey your contributions effectively. Words like "led," "developed," "managed," and "achieved" can make your summary more impactful.
    Highlight Relevant Skills
    Emphasize your core competencies that are directly applicable to the job. This can include technical skills, soft skills, and industry-specific knowledge.
    Showcase Your Value
    Explain how your background and skills can benefit the employer. Focus on what you can bring to the company rather than just listing your past roles.
    Maintain a Professional Tone
    Write in a professional and confident tone. Avoid using casual language or slang. Don't use first person.
    """
            system_message = st.text_area("AI Algorithm", value=st.session_state.ai_algorithm, height=200, key="ai_algorithm")
    
        with title_summary_col2:
            if st.session_state.job_desc_text:
                user_message = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Response"):
                st.session_state.summaries = generate_response(system_message, user_message)
                st.session_state.results += "Generated Summaries:\n" + st.session_state.summaries + "\n\n"
                st.text_area("Generated Summaries", value=st.session_state.summaries, height=200, key="generated_summaries_output")
                audio_html = play_audio()
                st.markdown(audio_html, unsafe_allow_html=True)
    
    st.subheader("Resume Summary Comparison")
    
    with st.container():
        col1, col2 = st.columns(2)
    
        with col1:
            if 'ai_algorithm2' not in st.session_state:
                st.session_state.ai_algorithm2 = """
    (1) Compare the Summaries to the Resume and write a best fit summary in the style of the Summaries keep it to 3 sentences and (2) indicate skill sets that are missing and training needed following the summary, keep it to 5 skills.
    """
            system_message2 = st.text_area("AI Algorithm Summary Refinement", value=st.session_state.ai_algorithm2, height=200, key="ai_algorithm2")
    
        with col2:
            if st.session_state.summaries and st.session_state.resume_text:
                user_message2 = "Summaries: " + st.session_state.summaries + " Resume: " + st.session_state.resume_text
                if st.button("Generate Summary Response"):
                    st.session_state.summary_response = generate_response(system_message2, user_message2)
                    st.session_state.results += "Summary Refinement:\n" + st.session_state.summary_response + "\n\n"
                    st.text_area("Summary Refinement", value=st.session_state.summary_response, height=200, key="summary_refinement_output")
            else:
                st.warning("Please generate the summaries and upload the resume to proceed.")
    
    st.subheader("Job Roles")
    
    with st.container():
        job_roles_col1, job_roles_col2 = st.columns([1, 1])
    
        with job_roles_col1:
            if 'ai_algorithm3' not in st.session_state:
                st.session_state.ai_algorithm3 = """ Job roles are defined as specific sets of responsibilities, tasks, and duties assigned to individuals within an organization. They outline what is expected of an employee in terms of their work functions and contributions. Examining the job description give 8 job roles.   
    """
            system_message3 = st.text_area("AI Algorithm Job Roles", value=st.session_state.ai_algorithm3, height=200, key="ai_algorithm3")
    
        with job_roles_col2:
            if st.session_state.job_desc_text:
                user_message = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Job Roles Response"):
                st.session_state.job_roles = generate_response(system_message3, user_message)
                st.session_state.results += "Generated Job Roles:\n" + st.session_state.job_roles + "\n\n"
                st.text_area("Generated Job Roles", value=st.session_state.job_roles, height=200, key="generated_job_roles_output")
    
    st.subheader("Technical Skills")
    
    with st.container():
        technical_col1, technical_col2 = st.columns([1, 1])
    
        with technical_col1:
            if 'ai_algorithm4' not in st.session_state:
                st.session_state.ai_algorithm4 = """ Extract the technical skills mentioned from the job description. List the keywords that represent the required technical skills needed to perform the job.   
    """
            system_message4 = st.text_area("AI Algorithm Technical Skills", value=st.session_state.ai_algorithm4, height=200, key="ai_algorithm4")
    
        with technical_col2:
            if st.session_state.job_desc_text:
                user_message = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Technical Skills Response"):
                st.session_state.technical = generate_response(system_message4, user_message)
                st.session_state.results += "Generated Technical Skills:\n" + st.session_state.technical + "\n\n"
                st.text_area("Generated Technical Skills", value=st.session_state.technical, height=200, key="generated_technical_output")
    
    st.subheader("Work History Critique")

    with st.container():
        history_col1, history_col2 = st.columns([1, 1])
    
        with history_col1:
            if 'ai_algorithm5' not in st.session_state:
                st.session_state.ai_algorithm5 = """  Critique Resume Work History. Include as much metrics and numbers as possible, when you are describing the impact. This will be especially useful when you take these stories and include them as bullet points on your resume! Below make a list of suggested changes. 
    """
            system_message5 = st.text_area("AI Algorithm History Critique", value=st.session_state.ai_algorithm5, height=200, key="ai_algorithm5")
    
        with history_col2:
            if st.session_state.resume_text:
                user_message5 = st.session_state.resume_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate History Critique"):
                st.session_state.history = generate_response(system_message5, user_message5)
                st.session_state.results += "Generated History Critique:\n" + st.session_state.history + "\n\n"
                st.text_area("Generated History Critique", value=st.session_state.history, height=200, key="generated_history_output")
    
    st.subheader("Education")
    
    with st.container():
        educational_col1, educational_col2 = st.columns([1, 1])
    
        with educational_col1:
            if 'ai_algorithm6' not in st.session_state:
                st.session_state.ai_algorithm6 = """ Provide any educational degrees required from the job description.   
    """
            system_message6 = st.text_area("AI Algorithm Education Skills", value=st.session_state.ai_algorithm6, height=200, key="ai_algorithm6")
    
        with educational_col2:
            if st.session_state.job_desc_text:
                user_message = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Educational Response"):
                st.session_state.educational = generate_response(system_message6, user_message)
                st.session_state.results += "Generated Required Education:\n" + st.session_state.educational + "\n\n"
                st.text_area("Generated Required Education", value=st.session_state.educational, height=200, key="generated_educational_output")
    
    st.subheader("Certifications")
    
    with st.container():
        certification_col1, certification_col2 = st.columns([1, 1])
    
        with certification_col1:
            if 'ai_algorithm7' not in st.session_state:
                st.session_state.ai_algorithm7 = """ Provide any certifications required from the job description.   
    """
            system_message7 = st.text_area("AI Algorithm Certification Skills", value=st.session_state.ai_algorithm7, height=200, key="ai_algorithm7")
    
        with certification_col2:
            if st.session_state.job_desc_text:
                user_message7 = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Certification Response"):
                st.session_state.certification = generate_response(system_message7, user_message7)
                st.session_state.results += "Generated Required Certification:\n" + st.session_state.certification + "\n\n"
                st.text_area("Generated Required Certification", value=st.session_state.certification, height=200, key="generated_certification_output")
    
    st.subheader("Cover Letter")
    
    with st.container():
        cover_col1, cover_col2 = st.columns([1, 1])
    
        with cover_col1:
            if 'ai_algorithm8' not in st.session_state:
                st.session_state.ai_algorithm8 = """ From the Job Description generate a cover letter for the template below 
                
Date

Hiring Manager’s Name

Company Name
Address
City, State, Zip Code
Dear [Hiring Manager’s Name/ Hiring Team],
[Attention-Grabbing Headline: Reflect the Company’s Mission]
Request Job Description, write from JOb Description
When I discovered your mission to [insert company mission or value], it resonated deeply with me. As someone who [describe a personal or professional connection to the company's mission], I admire how [Company Name] continually [describe a key achievement or quality of the company]. Witnessing your innovative approach to [specific industry or field] has inspired me to pursue this opportunity with you. The commitment to [specific value or goal of the company] aligns perfectly with my professional ethos and personal values.
[Passion and Problem-Solving Headline: Showcase Your Drive]
In my role as a [your current or previous role], I’ve tackled challenges such as [briefly describe a problem you solved]. This experience honed my skills in [key skills related to the job you’re applying for], and ignited my passion for [specific aspect of the job or industry]. At [Company Name], I see an opportunity to leverage my skills to contribute to [specific company goal or initiative]. The dynamic nature of [company’s industry] excites me, and I am driven to continuously adapt and innovate to meet evolving challenges.
[Narrative Example Headline: Illustrate Your Impact]
One of my proudest achievements was when I [describe a significant project or accomplishment]. For instance, while working at [previous company], I led a project that [describe the project briefly and its impact]. This experience underscored the importance of [relevant skill or value], and I am eager to bring this perspective to [Company Name]. I believe that my background in [relevant field or expertise] can help [Company Name] continue to thrive and innovate.
[Invitation to Connect: Show Enthusiasm]
I am excited about the possibility of joining [Company Name] and contributing to your mission of [restate the company’s mission or a specific goal]. I would love to discuss how my background, skills, and enthusiasm align with the needs of your team. Please feel free to contact me at [your email address] or [your phone number] to schedule a conversation. Thank you for considering my application. I look forward to the opportunity to further discuss how I can contribute to your team.
Sincerely,
[Your Name]

Key Points to Include:
Attention-Grabbing Headline: Start with a headline that reflects the company’s mission or a powerful company quote.
Personal Connection: Share why you feel connected to the company. Mention any personal or professional experiences that align with the company's values.
Passion and Problem-Solving: Explain what you do and why you’re passionate about it. Highlight the problems you solve and your motivation.
Narrative Example: Provide a brief narrative of a significant achievement related to your work and the job you’re applying for.
Invitation to Connect: Show enthusiasm for the role and invite the hiring manager to connect with you. Provide your contact information.
This structure, informed by the provided documents, aims to create a disruptive and engaging cover letter that stands out to hiring managers.

SHORTEN TO ONE PAGE CUT IN HALF   
    """
            system_message8 = st.text_area("AI Algorithm Cover Letter", value=st.session_state.ai_algorithm8, height=200, key="ai_algorithm8")
    
        with cover_col2:
            if st.session_state.job_desc_text:
                user_message8 = st.session_state.job_desc_text
            else:
                st.warning("Please upload a Job Description to proceed.")
    
            if st.button("Generate Cover Letter Response"):
                st.session_state.cover = generate_response(system_message8, user_message8)
                st.session_state.results += "Generated Cover Letter:\n" + st.session_state.cover + "\n\n"
                st.text_area("Generated Cover Letter", value=st.session_state.cover, height=200, key="generated_cover_output")
    
    with st.container():
        st.subheader("Results")
        st.text_area("Results", value=st.session_state.results, height=200, key="results_4me")
        st.download_button(
            label="Download Results",
            data=st.session_state.results,
            file_name="results.txt",
            mime="text/plain"
        )

with tab3:
    st.title("Automatic Resume Builder")
    with st.container():
        autoresume_col1, autoresume_col2 = st.columns([1, 1])
    
        with autoresume_col1:
            jd = st.text_area("Job Description Text", value=st.session_state.job_desc_text, height=200, key="job_description_text2")

        with autoresume_col2:
            rm = st.text_area("Resume Text", value=st.session_state.resume_text, height=200, key="resume_text2")

    with st.container():
        if st.session_state.resume_text:
            st.write(rm)


with tab4:
    st.title("Course Creator")
    st.write("""
        Welcome to the Course Creator section! This feature allows you to design and manage your courses. You can create new courses,
        edit existing ones, and organize them to suit your teaching or learning objectives.
    """)
    # Example form for course creation
    with st.form("create_course"):
        course_title = st.text_input("Course Title")
        course_description = st.text_area("Course Description")
        submit = st.form_submit_button("Create Course")
        if submit:
            st.write(f"Course '{course_title}' created successfully!")

with tab5:
    st.title("Scoring Utility")
    st.write("""
        Scoring resume against job description.
    """)