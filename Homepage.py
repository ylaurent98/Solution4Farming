
import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title='Homepage',page_icon='❇️', layout='wide', initial_sidebar_state='expanded')


import persists, Emissions_Dashboard as ED, Emissions_Calculator as EC, Pollution_Dashboard as PD



PAGES = {
        # "Home": home_page
        "Greenhouse Gas Emissions Calculator": EC,
        "Emmisions Dashboard": ED,
        "Pollution Dashboard": PD
    }

# def get_session_state_username():
#     return st.session_state('username')

def save_new_user_to_db(credentials):
    for user in credentials['usernames']:
        username = user
    name = credentials.get('usernames').get(username).get('name')
    email = credentials.get('usernames').get(username).get('email')
    password = credentials.get('usernames').get(username).get('password')

    conn=sqlite3.connect("S4F_database.db")
    cursor=conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Users (
                   usernames TEXT PRIMARY KEY,
                   name TEXT,
                   password TEXT,
                   email TEXT
                   )
    ''')
    cursor.execute("INSERT INTO Users(usernames, name, password, email) VALUES (?,?,?,?)", (username, name, password, email))
    conn.commit()
    conn.close()


def change_password(username, credentials):
    new_password=credentials.get("usernames").get(username).get('password')
    conn=sqlite3.connect("S4F_database.db")
    cursor=conn.cursor()
    cursor.execute("UPDATE Users SET password = ? WHERE usernames = ?", (new_password, username))
    conn.commit()
    conn.close()

def send_password_via_email(credentials, username, email, password):
    name = credentials.get('usernames').get(username).get('name')
    body=f"Hello {name}! Your password has been changed to {password}."
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = "Your password has been changed"
    msg['From'] = 'laurentyolanda@googlemail.com'
    msg['To'] = email

    # Gmail SMTP details
    GMAIL_HOST = 'smtp.gmail.com'
    GMAIL_PORT = 587
    GMAIL_USER = 'laurentyolanda@gmail.com'
    GMAIL_PASSWORD = 'kymhuewudpqyexwg'

    with smtplib.SMTP(GMAIL_HOST, GMAIL_PORT) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)





def hp_show():
    if 'authentication_status' not in st.session_state:
             st.session_state['authentication_status'] = None

    if st.session_state['authentication_status'] == True:
        with st.sidebar:
            st.write(f"Hi *{st.session_state['name']}*")

    # coll1,coll2=st.columns([3,2])
    # with coll1:
    st.title("Solution For Farming")
    with open ('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    # gradient_css = """
    # <style>
    # body {
    #     background: rgb(174,238,184);
    #     background: radial-gradient(circle, rgba(174,238,184,1) 0%, rgba(233,193,148,1) 100%);

    # }
    # </style>
    # """

    # st.markdown(gradient_css, unsafe_allow_html=True)

    conn=sqlite3.connect('S4F_database.db')
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM Users")
    rows=cursor.fetchall()

    # Create a dictionary with row IDs as keys and the rows as dictionary values
    all_users = {row['usernames']: dict(row) for row in rows}
    all_users= {'usernames':all_users}
    conn.close()

    ## still need to update database with user modifications/registations OR YAML file??
    ## https://medium.com/@HUSAM_007/streamlit-authentication-bf6385a71e78
    authenticator = stauth.Authenticate (credentials= all_users, cookie_name="dashboard", key = persists.persist("abcdef"))

    name=''
    username=''

    if st.session_state['authentication_status']==True:
            st.session_state['logout']=None
            authenticator.logout('Logout', 'sidebar', key='logout_button')
            if st.session_state['logout'] == True:
                st.session_state['authentication_status']=None
            # with open("pages/username", "w") as file:
            #     # Write the value from st.session_state['username'] to the file
            #     file.write(st.session_state['username'])


    name, st.session_state['authentication_status'], username = authenticator.login('Login', 'main')
    persists.persist(st.session_state['authentication_status'])
    persists.persist(username)
    if 'username' not in st.session_state:
            st.session_state['username'] = username

    if st.session_state['authentication_status'] == True:
            st.header(f'Welcome *{name}*')
            # st.session_state['authenticator'].logout('Logout', 'sidebar', key='unique_key')
            # st.write(f'Welcome *{name}*')
            col1, col2, col3 = st.columns(3, gap="large")
            with col1:
                #subheader_text = "🧮 Emisssions Calculator"
                url = "http://localhost:8501/Emissisons_Calculator"
                markdown_text = f"## [ Emisssions Calculator](url)"
                st.markdown(markdown_text, unsafe_allow_html=True)
                pic_link='https://static.vecteezy.com/system/resources/previews/002/766/981/large_2x/co2-emissions-calculation-rgb-color-icon-carbon-footprint-calculator-isolated-illustration-transportation-and-waste-estimating-carbon-dioxide-releases-simple-filled-line-drawing-vector.jpg'
                # st.markdown(f"[![Foo]({pic_link})](http://google.com.au/)")
                image_width = 100  # in pixels or use '%' for percentage
                image_height = 100  # in pixels or use '%' for percentage
                st.markdown(
                f'<a href={url}><img src="{pic_link}" width="100%" height="100%"></a>',
                unsafe_allow_html=True
                    )

            with col2:
                pic_link_2="https://img.freepik.com/premium-vector/pie-graph-icon-vector-flat-illustration-pie-chart-infographic-ui-business-presentation_547674-470.jpg?w=1480"
                url = "http://localhost:8501/Emissisons_Dashboard"
                markdown_text = f"## [ Emisssions Dashboard](url)"
                st.markdown(markdown_text, unsafe_allow_html=True)
                image_width = 250  # in pixels or use '%' for percentage
                image_height = 250  # in pixels or use '%' for percentage
                st.markdown(
                f'<a href={url}><img src="{pic_link_2}" width="100%" height="100%"></a>',
                unsafe_allow_html=True
                    )

            with col3:
                pic_link_3="https://thumbs.dreamstime.com/z/basic-cmyk-142414012.jpg?w=768"
                url = "http://localhost:8501/Pollution_Dashboard"
                markdown_text = f"## [ Pollution Dashboard](url)"
                st.markdown(markdown_text, unsafe_allow_html=True)
                image_width = 250  # in pixels or use '%' for percentage
                image_height = 250  # in pixels or use '%' for percentage
                st.markdown(
                f'<a href={url}><img src="{pic_link_3}" width="100%" height="100%"></a>',
                unsafe_allow_html=True
                    )


    elif st.session_state['authentication_status'] is False:
            st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
            st.warning('Please enter your username and password or sign-up below')
            try:
                if authenticator.register_user('Register user', preauthorization=False):
                    st.success('User registered successfully')
                    st.write(authenticator.credentials)
                    save_new_user_to_db(authenticator.credentials)
            except Exception as e:
                st.error(e)

        #Change passsword
    if st.session_state['authentication_status']:
            with st.expander("Click to change password"):
                try:
                    if authenticator.reset_password(username, 'Reset password'):
                        change_password(st.session_state['username'], authenticator.credentials)
                        st.success('Password modified successfully')
                except Exception as e:
                    st.error(e)

        #Forgot passssword
    if st.session_state['authentication_status'] == False:
            with st.expander("I forgot my passsword"):
                try:
                    username_forgot_pw, email_forgot_password, random_password = authenticator.forgot_password('Forgot password')
                    if username_forgot_pw:
                        st.success('New password sent securely')
                        change_password(username_forgot_pw, authenticator.credentials)
                        # Random password to be transferred to the user securely
                        send_password_via_email(authenticator.credentials, username_forgot_pw, email_forgot_password, random_password)

                    else:
                        st.error('Username not found')
                except Exception as e:
                    st.error(e)

def main():
    with st.sidebar:
        image_path = 'static/logo.png'
        # Display the image
        st.image(image_path,width=200)
    selection = st.sidebar.radio("Go to", [ "Home","Greenhouse Gas Emissions Calculator", "Emmisions Dashboard","Pollution Dashboard"])
#list(PAGES.keys())
    if selection =="Home":
        page='Home'
        hp_show()
    else:
        page = PAGES[selection]
        page.show()



if __name__ == "__main__":
    persists.load_widget_state()
    main()
