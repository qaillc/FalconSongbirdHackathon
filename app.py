import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import chardet
import time
import random
from io import BytesIO
from config import get_ai71_api_key
from audio import play_audio
from file_utils import extract_text_from_pdf as _extract_text_from_pdf, extract_text_from_word as _extract_text_from_word
from ai_utils import generate_response as _generate_response
from similarity import compare_summaries, rewrite_summary, identify_lacking_elements
from streamlit_navigation_bar import st_navbar
from requests.exceptions import HTTPError

# Set the page configuration to wide layout
st.set_page_config(layout="wide")

# Define the tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Introduction", "Manual Resume Assistant", "Automatic Resume Builder", "Course Creator", "Resume Scoring Utility","Job Search Utility"])

# Display the Introduction
with tab1:
    st.write("""
            Welcome to the Resume Builder! This tool is designed to help you create professional and polished resumes quickly and easily.
            Follow the steps in this guide to get started and learn how to use all the features of the Resume Builder.
        """)
    st.title("Introduction to Resume Builder")
    st.image("images/falconSB.png")
    # st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Replace with your video URL

# Manual Resume Assistant
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
            mime="text/plain",
            key="download_results_manual"
        )

# Automatic Resume Builder
with tab3:
    st.title("Automatic Resume Builder")
    
    def extract_job_desc(file):
        if file.type == "application/pdf":
            return _extract_text_from_pdf(file)
        elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return _extract_text_from_word(file)
        return ""
    
    def extract_resume(file):
        if file.type == "application/pdf":
            return _extract_text_from_pdf(file)
        elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return _extract_text_from_word(file)
        return ""
    
    def generate_summaries(job_desc):
        system_message = st.session_state.ai_algorithm
        return generate_response(system_message, job_desc)
    
    def refine_summary(summaries, resume):
        system_message2 = st.session_state.ai_algorithm2
        user_message = f"Summaries: {summaries} Resume: {resume}"
        return generate_response(system_message2, user_message)
    
    def identify_job_roles(job_desc):
        system_message3 = st.session_state.ai_algorithm3
        return generate_response(system_message3, job_desc)
    
    def extract_technical_skills(job_desc):
        system_message4 = st.session_state.ai_algorithm4
        return generate_response(system_message4, job_desc)
    
    def critique_work_history(resume):
        system_message5 = st.session_state.ai_algorithm5
        return generate_response(system_message5, resume)
    
    def identify_education_requirements(job_desc):
        system_message6 = st.session_state.ai_algorithm6
        return generate_response(system_message6, job_desc)
    
    def identify_certifications(job_desc):
        system_message7 = st.session_state.ai_algorithm7
        return generate_response(system_message7, job_desc)
    
    def generate_cover_letter(job_desc):
        system_message8 = st.session_state.ai_algorithm8
        return generate_response(system_message8, job_desc)
    
    # Execute the automatic resume building steps sequentially
    with st.container():
        autoresume_col1, autoresume_col2 = st.columns([1, 1])
    
        with autoresume_col1:
            job_desc_file = st.file_uploader("Upload Job Description (PDF or Word)", type=["pdf", "docx", "doc"], key="job_desc_uploader_auto")
            resume_file = st.file_uploader("Upload Resume (PDF or Word)", type=["pdf", "docx", "doc"], key="resume_uploader_auto")
    
        with autoresume_col2:
            if job_desc_file and resume_file:
                st.session_state.job_desc_text = extract_job_desc(job_desc_file)
                st.session_state.resume_text = extract_resume(resume_file)
    
                # Run the resume building steps sequentially
                summaries = generate_summaries(st.session_state.job_desc_text)
                refined_summary = refine_summary(summaries, st.session_state.resume_text)
                job_roles = identify_job_roles(st.session_state.job_desc_text)
                technical_skills = extract_technical_skills(st.session_state.job_desc_text)
                work_history_critique = critique_work_history(st.session_state.resume_text)
                education_requirements = identify_education_requirements(st.session_state.job_desc_text)
                certifications = identify_certifications(st.session_state.job_desc_text)
                cover_letter = generate_cover_letter(st.session_state.job_desc_text)
    
                # Combine results
                results = (
                    f"Generated Summaries:\n{summaries}\n\n"
                    f"Refined Summary:\n{refined_summary}\n\n"
                    f"Job Roles:\n{job_roles}\n\n"
                    f"Technical Skills:\n{technical_skills}\n\n"
                    f"Work History Critique:\n{work_history_critique}\n\n"
                    f"Educational Requirements:\n{education_requirements}\n\n"
                    f"Certifications:\n{certifications}\n\n"
                    f"Cover Letter:\n{cover_letter}\n\n"
                )
                
                st.session_state.results += "Automatic Resume Building Results:\n" + results + "\n\n"
                st.text_area("Automatic Resume Building Results", value=st.session_state.results, height=200, key="automatic_resume_results")
    
    with st.container():
        st.subheader("Results")
        st.text_area("Results", value=st.session_state.results, height=200, key="results_4me_auto")
        st.download_button(
            label="Download Results",
            data=st.session_state.results,
            file_name="results.txt",
            mime="text/plain",
            key="download_results_auto"
        )

# Course Creator
with tab4:
    st.title("Course Creator")

    # Initialize session state if not already done
    if 'ai_algorithm10' not in st.session_state:
        st.session_state.ai_algorithm10 = """for the course in the prompt create a 10 parts hands on zero to hero course. Outline the theory and labs in sufficient detail"""
    
    def generate_course(coursename):
        system_message8 = st.session_state.ai_algorithm10
        return generate_response(system_message8, coursename)
    

    st.title("10-Part Hands-On Course Generator")
    
    st.write("""
    This application generates a 10-part hands-on zero-to-hero course.
    You can enter the course topic you are interested in or use the default course.
    """)
    
    # Input for course name
    course_name = st.text_input("Enter the course name (default: scikit-learn)", "scikit-learn")
    
    # Button to generate course
    if st.button("Generate Course"):
        course_content = generate_course(course_name)
        st.text_area("Generated Course Content", course_content, height=300)


# Job Search Utility
with tab5:
    st.title("Resume Scoring Utility")
    st.write("""
        Score your resume, improve it, and score again!
    """)

    url = "https://chatgpt.com/g/g-VjyElg53f-resume-scorer"
    st.markdown(f"[Score Resume]({url})")

    # Initialize session state if not already done
    if 'ai_algorithm11' not in st.session_state:
        st.session_state.ai_algorithm11 = """

From the Resume and Job Description in the prompt Score them based on the rules below:

Job Description vs Resume Comparison Tool Rubric

1. ATS Compatibility (20% of overall score)
   - Measures how well the resume matches keywords from the job description
   - Ignores common words (e.g., "the," "and," "or") and is case-insensitive
   - Focuses on industry-specific terms, job titles, and technical skills
   - Score calculation: (Matched keywords) / (Total keywords) * 100%
   - Example: If 15 out of 20 key terms match, the score would be (15/20) * 100% = 75%

2. Skills Match (30% of overall score)
   - Compares skills mentioned in the job description to those in the resume
   - Uses a predefined list of technical skills (e.g., programming languages, software) and soft skills (e.g., communication, leadership)
   - Considers both explicitly stated skills and those implied by experience
   - Score calculation: (Matched skills) / (Required skills) * 100%
   - Example: If 8 out of 10 required skills are matched, the score would be (8/10) * 100% = 80%

3. Experience Relevance (25% of overall score)
   - Considers both years of experience and keyword relevance in work history
   - Years of experience calculation: Min(Resume years / Required years, 1) * 60%
     - This caps the score at 100% if the candidate exceeds the required experience
   - Keyword relevance calculation: (Matched keywords) / (Total keywords) * 40%
   - Overall score: (Years score + Relevance score) * 100%
   - Example: If a candidate has 5 years experience (requirement: 3 years) and matches 7 out of 10 keywords:
     Years score: Min(5/3, 1) * 60% = 60%
     Relevance score: (7/10) * 40% = 28%
     Overall score: (60% + 28%) * 100% = 88%

4. Education Alignment (15% of overall score)
   - Evaluates both degree level and field of study
   - Degree level calculation: Min(Resume degree level / Required degree level, 1) * 70%
     - Degree levels are assigned numerical values (e.g., Bachelor's = 1, Master's = 2, PhD = 3)
   - Field of study calculation: (Matched fields) / (Required fields) * 30%
   - Score: (Degree level score + Field score) * 100%
   - Example: If a Master's is required (level 2) and the candidate has a PhD (level 3) in the exact field:
     Degree level: Min(3/2, 1) * 70% = 70%
     Field of study: (1/1) * 30% = 30%
     Overall score: (70% + 30%) * 100% = 100%

5. Key Achievements (10% of overall score)
   - Looks for achievement keywords (e.g., "increased," "improved," "led") and quantitative results
   - Achievement keywords calculation: (Matched keywords) / (Total keywords) * 60%
   - Quantitative results calculation: Min(Number of quantitative matches / 3, 1) * 40%
     - This caps the score at 100% if there are 3 or more quantitative achievements
   - Score: (Keyword score + Quantitative score) * 100%
   - Example: If 4 out of 5 achievement keywords match and there are 2 quantitative results:
     Keywords: (4/5) * 60% = 48%
     Quantitative: (2/3) * 40% = 26.67%
     Overall score: (48% + 26.67%) * 100% = 74.67%

Overall Score Calculation:
- Sum of (Category Score * Category Weight) for all categories
- Example: (ATS * 20%) + (Skills * 30%) + (Experience * 25%) + (Education * 15%) + (Achievements * 10%)

Score Interpretation:
- 80% or higher: Good match (Green) - The resume aligns well with the job requirements
- 60% to 79%: Moderate match (Yellow) - The resume meets some key requirements but may lack in certain areas
- Below 60%: Poor match (Red) - The resume does not adequately match the job requirements

Note: This rubric is based on automated keyword matching and quantitative analysis. It should be used as a preliminary screening tool to identify potentially strong candidates. However, it may not capture all nuances of a candidate's qualifications, such as quality of experience, cultural fit, or unique skills not explicitly mentioned. Human evaluation is crucial for a comprehensive assessment of a candidate's suitability for the position.
        
        """

    def generate_response(system_message, jd_resume):
        # Placeholder for actual API call or algorithm
        # Here you should set the correct headers for your request if using an API
        headers = {
            'Content-Type': 'text/event-stream'
        }
        # Simulate response for example purposes
        return "Simulated response based on: " + system_message + " and " + jd_resume
    
    def extract_job_desc(file):
        # Placeholder function for extracting job description text
        return "Extracted job description text."
    
    def extract_resume(file):
        # Placeholder function for extracting resume text
        return "Extracted resume text."
    
    def generate_score(jd_resume):
        system_message11 = st.session_state.ai_algorithm11
        return generate_response(system_message11, jd_resume)
    
    job_desc_file = st.file_uploader("Upload Job Description (PDF or Word)", type=["pdf", "docx", "doc"], key="job_desc_uploader_auto_score")
    resume_file = st.file_uploader("Upload Resume (PDF or Word)", type=["pdf", "docx", "doc"], key="resume_uploader_auto_score")
    
    if job_desc_file and resume_file:
        try:
            # Detect encoding and read the files
            job_desc_content = extract_job_desc(job_desc_file)
            resume_content = extract_resume(resume_file)
            
            # Combine the contents of both files
            jd_resume = f"Job Description:\n{job_desc_content}\n\nResume:\n{resume_content}"
            
            # Button to generate the score
            if st.button("Score Resume"):
                score_content = generate_score(jd_resume)
                st.text_area("Generated Course Content", score_content, height=400)
        except Exception as e:
            st.write(f"Error reading files: {e}")
    else:
        st.write("Please upload both the job description and the resume.")

    
# Job Search Utility
with tab6:


    def scrape_linkedin_jobs(keyword, location, num_pages=1):
        base_url = "https://www.linkedin.com/jobs/search/"
        jobs = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
        for page in range(num_pages):
            params = {
                "keywords": keyword,
                "location": location,
                "start": page * 10
            }
            
            try:
                response = requests.get(base_url, params=params, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = soup.find_all('div', class_='base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card')
                
                if not job_cards:
                    st.warning(f"No job cards found on page {page + 1}. The page structure might have changed.")
                    continue
    
                for card in job_cards:
                    title = card.find('h3', class_='base-search-card__title')
                    company = card.find('h4', class_='base-search-card__subtitle')
                    location = card.find('span', class_='job-search-card__location')
                    link = card.find('a', class_='base-card__full-link')
                    
                    if title and company and location and link:
                        jobs.append({
                            'Title': title.text.strip(),
                            'Company': company.text.strip(),
                            'Location': location.text.strip(),
                            'Link': link['href']
                        })
                
                time.sleep(random.uniform(1, 3))  # Random delay between requests
            
            except requests.RequestException as e:
                st.error(f"An error occurred while fetching page {page + 1}: {str(e)}")
                break
    
        return jobs
    
    st.title("LinkedIn Job Scraper")
    
    keyword = st.text_input("Enter job keyword:", value="prompt engineer")
    location = st.text_input("Enter location:", value="Ohio USA")
    num_pages = st.number_input("Number of pages to scrape:", min_value=1, max_value=10, value=1)
    
    if st.button("Scrape Jobs"):
        if keyword and location:
            with st.spinner('Scraping jobs... This may take a moment.'):
                jobs = scrape_linkedin_jobs(keyword, location, num_pages)
            if jobs:
                df = pd.DataFrame(jobs)
                st.success(f"Found {len(jobs)} jobs!")
                st.dataframe(df)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="linkedin_jobs.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No jobs found. Try different keywords or location.")
        else:
            st.warning("Please enter both keyword and location.")
    
    st.markdown("---")
    st.markdown("Note: This scraper is for educational purposes only. Please respect LinkedIn's terms of service.")
