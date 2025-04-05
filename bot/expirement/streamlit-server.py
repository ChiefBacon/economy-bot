import streamlit as st
from time import sleep, time
from datetime import datetime, timezone
from sqlalchemy.sql import text

cache_time = "0"

# Initialize connection.
conn = st.connection("postgresql", type="sql")


def log_transaction(session, sender: str, recepient: str, amount: float, note: str):
    session.execute(text('INSERT INTO Transactions VALUES (:t, :f, :x, :y, :z);'), {"t": datetime.now(timezone.utc),"f": sender, "x": recepient, "y": amount, "z": note})

def check_user_exists(username: str):
    user_exists = conn.query('SELECT EXISTS (SELECT 1 FROM users WHERE username=:x);', params = {"x": username}, ttl = cache_time)
    return user_exists.get("exists").array[0]

def get_user_data(username: str):
    userdata = conn.query('SELECT * FROM users WHERE username=:x;', params = {"x": username}, ttl = cache_time)
    return userdata.to_numpy()[0]

def set_user_bal(session, username: str, new_balance: float):
    session.execute(text('UPDATE Users SET Balance = :x WHERE username=:y;'), {"x": new_balance, "y": username})

def change_user_bal(session, username: str, change: float):
    session.execute(text('UPDATE Users SET Balance = Balance + :x WHERE username=:y;'), {"x": change, "y": username})


def page1func():
    st.title("Economy Bot")
    if 'username' in st.session_state:
            st.switch_page(home_page)
    
    with st.form("login"):
        st.write("Please log in")
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')

        # Every form must have a submit button.
        submitted = st.form_submit_button("Login")
        if submitted:
            user_exists = conn.query('SELECT EXISTS (SELECT 1 FROM users WHERE username=:x AND password=:y);', params = {"x": username, "y": password}, ttl = cache_time)
            if user_exists.get("exists").array[0]:
                parsed_userdata = get_user_data(username)
                st.session_state['parsed_user_data'] = parsed_userdata
                st.session_state['user_is_admin'] = parsed_userdata[3]
                st.session_state['username'] = username
                st.session_state['password'] = password
                st.switch_page(home_page)
            else:
                st.error("Invalid Username or Password\n(Your acct. may not be set up for web access)", icon="⚠️")

def log_out():
    if 'username' in st.session_state:
        st.session_state.pop('username')
        st.session_state.pop('password')
    st.rerun()


def home():
    if 'username' not in st.session_state:
        st.switch_page(login)
    parsed_userdata = get_user_data(st.session_state['username'])
    st.write(f"# Welcome {parsed_userdata[1]}!\n### Your current balance is {parsed_userdata[2]}🪙")
    transactions = conn.query('SELECT * FROM transactions WHERE fromdiscordid=:x OR todiscordid=:x', params= {"x": parsed_userdata[0]})
    st.write("#### Your Recent Transactions")
    st.dataframe(transactions)

def send_money():
    if 'username' not in st.session_state:
        st.switch_page(login)
    parsed_userdata = get_user_data(st.session_state['username'])
    with st.form('send_money'):
        username_to_send_to = st.text_input('Recepient')
        ammt_to_send = st.number_input('Amount', value= 0.0, min_value=0.0)
        submitted = st.form_submit_button("Send!")
        if submitted:
            if check_user_exists(username_to_send_to):
                user_to_send_to_data = get_user_data(username_to_send_to)
                if parsed_userdata[2] >= ammt_to_send:
                    with conn.session as session:
                        change_user_bal(session, parsed_userdata[1], ammt_to_send * -1) 
                        change_user_bal(session, username_to_send_to, ammt_to_send)
                        log_transaction(session, user_to_send_to_data[0], parsed_userdata[0], ammt_to_send, "User Money Transfer")
                        session.commit()
                    st.success(f"Sent {ammt_to_send}🪙 to {username_to_send_to}", icon="✅")
            else:
                st.error("User Does Not Exist!", icon="⚠️")

def change_password():
    if 'username' not in st.session_state:
        st.switch_page(login)
    parsed_userdata = get_user_data(st.session_state['username'])
    with st.form('change_pass'):
        current_pass = st.text_input('Current Password', type='password')
        new_password = st.text_input('New Password', type='password')
        new_password_confirm = st.text_input('Confirm New Password', type='password')
        submitted = st.form_submit_button("Change")
        if submitted and current_pass and new_password and new_password_confirm:
            if new_password == new_password_confirm:
                if current_pass == parsed_userdata[4]:
                    st.session_state['passwd_changed'] = True
                    with conn.session as session:
                        session.execute(text('UPDATE Users SET password=:x WHERE username=:y;'), {"x": new_password, "y": parsed_userdata[1]})
                        session.commit()
                    st.switch_page(login)
                else:
                    st.error("Invalid Password", icon="⚠️")
            else:
                st.error("Passwords do not match", icon="⚠️")
    
def transaction_check():
    if 'username' not in st.session_state:
        st.switch_page(login)
    st.write("# Database")
    userdata = conn.query('SELECT * FROM transactions', ttl = cache_time)
    st.dataframe(userdata)

def add_money_to_all():
    if 'username' not in st.session_state:
        st.switch_page(login)
    st.write("# Add Money To All Users")
    with st.form('add_money_all'):
        ammt = st.number_input('Amount', value= 0.0, min_value=0.0)
        submitted = st.form_submit_button("Add")
        if submitted:
            with conn.session as session:
                    session.execute(text('UPDATE Users SET Balance = Balance + :x;'), {"x": ammt})
                    log_transaction(session, 'system', 'all', ammt, "Admin Adding Money To All")
                    session.commit()
            st.success(f"{ammt}🪙 Added To All Users", icon="✅")

def add_money():
    if 'username' not in st.session_state:
        st.switch_page(login)
    st.write("# Add Money")
    with st.form('add_money_all'):
        ammt = st.number_input('Amount', value= 0.0, min_value=0.0)
        user_to_add_to = st.text_input("User To Add To")
        submitted = st.form_submit_button("Add")
        if submitted:
            if check_user_exists(user_to_add_to):
                user_to_add_to_data = get_user_data(user_to_add_to)
                with conn.session as session:
                    change_user_bal(session, user_to_add_to, ammt)
                    log_transaction(session, 'system', user_to_add_to_data[0], ammt, "Admin Adding Money")
                    session.commit()
                st.success(f"{ammt}🪙 Added To {user_to_add_to}", icon="✅")
            else:
                st.error("User Does Not Exist!", icon="⚠️")

login = st.Page(page1func, title="Login", icon="🪙")
home_page = st.Page(home, title="Home", icon=":material/home:")
log_out_page = st.Page(log_out, title="Log Out", icon=":material/logout:")
send_money_page = st.Page(send_money, title="Send Money", icon=":material/send:")
transaction_check_page = st.Page(transaction_check, title="Transaction Viewer", icon=":material/database:")
change_password_page = st.Page(change_password, title="Change Password", icon=":material/key:")
add_money_to_all_page = st.Page(add_money_to_all, title="Add Money To All", icon=":material/payments:")
add_money_page = st.Page(add_money, title="Add Money", icon=":material/add:")

member_area = [home_page, send_money_page]
admin_pages = [transaction_check_page, add_money_to_all_page, add_money_page]
account_pages = [log_out_page, change_password_page]

page_dict = {}

if 'username' in st.session_state:
    page_dict = {"Memeber Area": member_area}
if 'user_is_admin' in st.session_state and 'username' in st.session_state:
    if st.session_state['user_is_admin']:
        page_dict.update({"Admin": admin_pages})
        
if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([login])

pg.run()