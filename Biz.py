import easyocr
import re
from PIL import Image
import numpy as np
import pandas as pd
import time
import psycopg2
import streamlit as st



# Setting Webpage Configurations
st.set_page_config(page_icon="💻", page_title="BisCardX✔️", layout="wide")


appview_bg_color = "#3A083E"
# Apply the background color using st.markdown

page_bg_color = f"""
<style>
        [data-testid="stAppViewContainer"] > .main {{
            background-color: {appview_bg_color};
            background-size: 180%;
            background-position: top left;
            background-repeat: no-repeat;
            background-attachment: local;
        }}

        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}

        [data-testid="stToolbar"] {{
            right: 2rem;
        }}
    </style>
"""


# Apply the background color using st.markdown
st.markdown(page_bg_color, unsafe_allow_html=True)
# Title
st.title(':red[BisCardX]')

# Extract information
@st.cache_data
def extract(upload):
    images = Image.open(upload)

    black_image = images.convert('L')
    black_img_np = np.array(black_image)
    read = easyocr.Reader(['en'])
    result = read.readtext(black_img_np, detail=0)

    phone_list = []

    # Patterns
    phonepattern = re.compile(r'\+|[0-9]+[-\s][0-9]+[-\s][0-9]+')
    webpattern = re.compile(r'[Ww]{3}')
    mailpattern = re.compile(r'@')
    addpattern = re.compile(r'\d+\s[a-zA-Z]+')
    pinpattern = re.compile(r'\d{5,6}|(\d{3}\s\d{3})')

    names = result[0]
    designations = result[1]

    for i in result:
        phone = phonepattern.search(i)
        if phone:
            phone_list.append(i)

    for i in result:
        mail = mailpattern.search(i)
        if mail:
            mail_id = i

    for i in result:
        web = webpattern.search(i)
        if web:
            websites = i

    for i in result:
        add = addpattern.search(i)
        if add:
            addresss = i

    for i in result:
        pin = pinpattern.finditer(i)
        for i in pin:
            pincodes = i.group()

    return names, designations, '|'.join(phone_list), mail_id, websites, addresss, pincodes



tab1,tab2,tab3 = st.tabs([':orange[UPLOAD | EXTRACT]',':blue[UPLOAD EXTRACTED DATA INTO POSTGRESQL]',':violet[VIEW | UPDATE | DELETE]' ])
# Upload | Extract
with tab1:
    # Uploader
    file_uploader = st.file_uploader('Upload your Image',accept_multiple_files = False)
    
    if file_uploader is not None:
        image = Image.open(file_uploader)
        resized_image = image.resize((500,250))
        
        if image is not None:  
            st.subheader('Image Preview') 
            st.image(resized_image)

    extract_button = st.button('Extract') 
    extract_progress_text = "Extraction in progress."

    # Extracted Information
    if extract_button:
        with st.spinner('Please Wait...'):

            name,designation,phone_no,email_id,website,address,pincode = extract(file_uploader)
    
            data = [name,designation,phone_no,email_id,website,address,pincode]
            list1 = []
            list1.append(data)  

            
            extract_bar = st.progress(0, text=extract_progress_text)
            for percent_complete in range(100):
                time.sleep(0.05)
                extract_bar.progress(percent_complete + 1, text=extract_progress_text)

            df = pd.DataFrame(list1,columns = ['Name','Designation','Phone_no','Email_id','Website','Address','Pincode'])
            st.dataframe(df)  
                
            st.subheader(f':red[Name] : {name}')
            st.subheader(f':red[Designation] : {designation}')
            st.subheader(f':red[Phone no] : {phone_no}')
            st.subheader(f':red[Email_id] : {email_id}')
            st.subheader(f':red[Website] : {website}')
            st.subheader(f':red[Address] : {address}')
            st.subheader(f':red[Pincode] : {pincode}')
            st.success("Data Extracted Successfully !!",icon="✅")
            st.balloons()


# Insert into PostgreSql Database
with tab2:
    try:
        sql = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="Jesikather@1206",
            database="Bizcard",  # Connect directly to the specified database
            port="5432")
    except:
        print('Please Check your internet Connection')
        
        
    mycursor = sql.cursor()

    # Check if the table exists, create it if not
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS bizcard_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            designation VARCHAR(255),
            phone_no VARCHAR(30),
            website VARCHAR(255),
            mail_id VARCHAR(255),
            address VARCHAR(255),
            pincode VARCHAR(10),
            password VARCHAR(255)
        )
    """)
    
    # Commit the changes
    sql.commit()
    
    # Your Streamlit code
    st.subheader(':red[Upload extracted data into postgresql]')
    id = st.text_input('Create a User Id')
    password = st.text_input('Create a Password', type="password")
    
    submit1 = st.button('Upload into PostgreSQL')

if submit1:
    with st.spinner('Please wait...'):
        # Extract data (you need to define the 'extract' function)
        name, designation, phone_no, email_id, website, address, pincode = extract(file_uploader)

        # Insert data into the table
        query = '''
            INSERT INTO bizcard_data (name, designation, phone_no, website, mail_id, address, pincode, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (name, designation, phone_no, website, email_id, address, pincode, password)

        mycursor.execute(query, values)
        sql.commit()

        st.success("Data uploaded successfully!", icon="✅")
        st.balloons()

    
# View | Update | Delete    
with tab3:
    your_id = st.text_input('Enter your Id')
    your_password = st.text_input('Enter your Password')

    submit2 = st.button('View Details')

    
    if your_id and your_password is not None:
        if submit2:
            with st.spinner('Please wait..'):
                try:
                    # Convert your_id to an integer
                    your_id = int(your_id)

                    query1 = 'select name,designation,phone_no,website,mail_id,address,pincode from bizcard_data where id = %s and password = %s;'
                    values = (your_id, your_password)
                    mycursor.execute(query1, values)
                    row_data = mycursor.fetchall()

                    if row_data:
                        st.image(resized_image)
                        df = pd.DataFrame(row_data, columns=["name", "designation", "phone_no", "website", "mail_id", "address", "pincode"], index=range(1, len(row_data) + 1))
                        st.dataframe(df)
                        st.success("Data fetched successfully", icon="✅")
                        st.balloons()
                    else:
                        st.warning("Data  found for the provided ID and password.")
                    
                    
                except ValueError:
                    st.error("Invalid ID. Please enter a valid integer ID.")
                    
                st.subheader(':red[Update your details]')

    select_options = st.selectbox('select any one field that you want to update',options=['Select any one','name','designation','phone_no','website','mail_id','address','pincode'])

    if select_options == 'name':
        name = st.text_input('Enter your name')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET name = %s WHERE id = %s and password = %s;'
            values = (name,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'designation':
        designation = st.text_input('Enter your designation')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET designation = %s WHERE id = %s and password = %s;'
            values = (designation,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'phone_no':
        phone_no = st.text_input('Enter your phone_no')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET phone_no = %s WHERE id = %s and password = %s;'
            values = (phone_no,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'website':
        website = st.text_input('Enter your phone_no')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET website = %s WHERE id = %s and password = %s;'
            values = (website,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'mail_id':
        mail_id = st.text_input('Enter your mail_id')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET mail_id = %s WHERE id = %s and password = %s;'
            values = (mail_id,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'address':
        address = st.text_input('Enter your address')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET address = %s WHERE id = %s and password = %s;'
            values = (address,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    elif select_options == 'pincode':
        pincode = st.text_input('Enter your pincode')
        update = st.button('Update your details')
        if update:
            update_query = 'UPDATE bizcard_data SET pincode = %s WHERE id = %s and password = %s;'
            values = (pincode,your_id,your_password)
            mycursor.execute(update_query,values)
            sql.commit()
            st.success('Data Updated Successfully',icon="✅")

    st.subheader(':red[Delete your details]')
    delete_id = st.text_input('Enter your id')
    delete = st.button('Delete your details')
    if delete:
        with st.spinner('Please wait..'):
            delete_query = 'DELETE FROM bizcard_data where id = %s;'
            values = (delete_id,)
            mycursor.execute(delete_query,values)
            sql.commit()
            st.success('Data deleted Successfully',icon="✅")