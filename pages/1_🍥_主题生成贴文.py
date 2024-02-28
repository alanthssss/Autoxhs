import streamlit as st
import datetime
from config.settings import text_models,image_models
from dotenv import load_dotenv
from time import sleep
from api.xhs_api import QRCode_sign_streamlit,cookie_sign
from api.openai_api import OpenAIClient
from api.langchain_api import LangChainClient,autoCategorize
from content.content_generator import *
from image.image_generator import get_image_langchain
from utils import *
from copy import deepcopy
from config.category import categoryTranslations
# load_dotenv(override=True)
# api_key = os.environ.get("OPENAI_API_KEY")
prompt_version = 'v1'
st.set_page_config(
    page_title="主题生成贴文",
    page_icon="🍥",
    layout="wide",
    initial_sidebar_state="expanded",
)
col1, col2 = st.columns([1,1]) 

if 'theme_input' not in st.session_state:
    st.session_state.theme_input = False
    
if 'suggestion_input' not in st.session_state:
    st.session_state.suggestion_input = False    

if 'title_generate_clicked' not in st.session_state:
    st.session_state.title_generate_clicked = False  # 初始化点击状态

if 'content_generate_clicked' not in st.session_state:
    st.session_state.content_generate_clicked = False  # 初始化点击状态
    
if 'content' not in st.session_state:
    st.session_state.content = None  

if 'title_list' not in st.session_state:
    st.session_state.title_list = []  
    
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False

with open("data/tools.json", 'r') as file:
    st.session_state.tools = json.load(file)

def create_langchain_client():

    if 'openai_api_key' in st.session_state and 'text_model' in st.session_state \
        and 'image_model' in st.session_state:
        # 创建新的LangChainClient实例
        
        st.session_state.langchain_client = LangChainClient(
            st.session_state.openai_api_key,
            st.session_state.image_model,
            st.session_state.text_model,
            st.session_state.tools
        ) 
        
    st.session_state.title_list = []  
    st.session_state.content = None 
    st.session_state.theme_input = False
    st.session_state.suggestion_input = False 
    st.session_state.title_generate_clicked = False
    st.session_state.content_generate_clicked = False
    
with st.sidebar: 
  
    st.title('登陆小红书')
    if st.session_state.user_logged_in:
        st.success("欢迎回来！您已成功登录。")
    else:
        st.session_state.xhs_client, qr_img, qr_res = QRCode_sign_streamlit()
        st.image(qr_img, caption='请扫描二维码完成登录',width =200)
        qr_id = qr_res["qr_id"]
        qr_code = qr_res["code"]
        while True:
            check_qrcode = st.session_state.xhs_client.check_qrcode(qr_id, qr_code)
            print(check_qrcode)
            sleep(1)
            if check_qrcode["code_status"] == 2:
                print(json.dumps(check_qrcode["login_info"], indent=4))
                print("当前 cookie：" + st.session_state.xhs_client.cookie)
                break
        st.session_state.user_logged_in = True
        st.rerun()

    
    openai_api_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        on_change=create_langchain_client,
        key='openai_api_key'  # 使用key参数确保值被正确存储在session_state中
    )
    
    text_model = st.selectbox(
        'Text Model', 
        text_models,
        on_change=create_langchain_client,
        key='text_model'
    )
    
    image_model = st.selectbox(
        'Image Model', 
        image_models,
        on_change=create_langchain_client,
        key='image_model'
    )
        
    categoryList = ["自动选择"]+list(categoryTranslations.keys())
    category = st.selectbox(
            '贴文类别', 
            categoryList,
            key='category',
        )

with col1:
    st.markdown("<h2 style='text-align: center; color: grey;'>📝 内容创作台</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
    # 生成标题列表
    # st.write("---")
        st.markdown("### 🏷️ 标题生成", unsafe_allow_html=True)
        theme = st.text_input('输入您的贴文主题：')
        if theme:
            st.session_state.theme_input = True

        if st.button("生成标题",disabled = not st.session_state.theme_input) and st.session_state.user_logged_in and st.session_state.theme_input:
            with st.spinner('请稍候，标题生成中...'):
                st.session_state.title_generate_clicked = True
                st.session_state.langchain_client.cleam_memory(0)
            
                if st.session_state.category=="自动选择" :
                    auto_selected_category = autoCategorize(theme, st.session_state.text_model,st.session_state.openai_api_key)
                    print("Auto selected category is " + auto_selected_category if auto_selected_category else "No category selected")
                    if auto_selected_category in categoryTranslations.keys():
                        with open('data/prompt/theme/{}.md'.format(categoryTranslations[auto_selected_category]), 'r', encoding='utf-8') as file:
                            st.session_state.system_prompt = file.read() 
                    else:
                        with open('data/prompt/theme/{}.md'.format("Default"), 'r', encoding='utf-8') as file:
                            st.session_state.system_prompt = file.read() 
                else:
                    with open('data/prompt/theme/{}.md'.format(categoryTranslations[st.session_state.category]), 'r', encoding='utf-8') as file:
                        st.session_state.system_prompt = file.read() 
                st.session_state.title_list = get_title_langchain(st.session_state.langchain_client, st.session_state.system_prompt,theme)
            st.success('标题列表已更新，请选择您喜欢的标题。')
            
    with st.container(border=True):
    # st.write("---")
        st.markdown("### ✍️ 贴文生成", unsafe_allow_html=True)

        selected_option = st.selectbox('选择一个标题开始创作：', st.session_state.title_list)
        if selected_option:
            st.session_state.selected_title = selected_option
                
        if st.button("生成贴文",disabled = not st.session_state.title_generate_clicked) and st.session_state.title_generate_clicked:
            with st.spinner('请稍候，自动生成中...'):
                st.session_state.content_generate_clicked = True
                st.session_state.langchain_client.cleam_memory(2)
                content = get_content_from_title_langchain(st.session_state.langchain_client,st.session_state.system_prompt, st.session_state.selected_title)
                
                success = st.success('文本内容生成成功！')

                st.session_state.save_path = create_directory_for_post()

                st.session_state.images = [
                    get_image_langchain(st.session_state.langchain_client, st.session_state.selected_title,st.session_state.save_path)
                ]
                
                success.empty()
                success = st.success('图片内容生成成功！')
                
                st.session_state.content = content
            success.empty()
            success = st.success('贴文内容已生成，可以预览并进行调整。')
            
    with st.container(border=True):
    # st.write("---") 
        st.markdown("### 🔄 贴文修改", unsafe_allow_html=True)
        
        suggestion = st.text_input('需要做出哪些调整？',disabled = not st.session_state.content_generate_clicked)
        if suggestion:
            st.session_state.suggestion_input = True
        if st.button("重新生成贴文",disabled = not st.session_state.suggestion_input) and st.session_state.content_generate_clicked and st.session_state.suggestion_input:
            with st.spinner('请稍候，重新生成中...'):
                content = get_content_from_suggestion_langchain(st.session_state.langchain_client,st.session_state.system_prompt,suggestion)
                st.session_state.content = content
            st.success('贴文已更新，感谢您的反馈！')
    
    if st.session_state.content: 
        note_data =  {
                "title": st.session_state.content['标题'],
                "description": st.session_state.content['正文'],
                "topics": st.session_state.content['Tags']
            }          
        note_md = trans_into_md(note_data)
        col2_1, col2_2,col2_3 = col2.columns([1,4,1])  
        with col2_2:
        # 将发布的贴文详情显示在主页面的右侧
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center; color: grey;'>📊 贴文预览</h2>", unsafe_allow_html=True)
                for image_path in st.session_state.images:
                    st.image(image_path, use_column_width=True)
                st.markdown(note_md, unsafe_allow_html=True)
                
    with st.container(border=True):
    # st.write("---")
        st.markdown("### 🚀 预览与发布",unsafe_allow_html=True)
        if st.button("发布到小红书",disabled = not st.session_state.content):
            with st.spinner('请稍候，自动发布中...'):
                post_content = deepcopy(st.session_state.content)
                topics = get_topics(st.session_state.xhs_client, post_content['Tags'])
                topics_suffix = get_topics_suffix(topics)
                post_content['正文'] = post_content['正文'] + topics_suffix

                note_info = st.session_state.xhs_client.create_image_note(
                    post_content['标题'], post_content['正文'], st.session_state.images, topics=topics, 
                    is_private=True, post_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                beauty_print(note_info)

                note_data = {
                    "title": post_content['标题'],
                    "description": post_content['正文'],
                    "topics": topics_suffix,
                    # 添加其他任何您想保存的信息
                }
                
                save_post_to_file(note_data, st.session_state.save_path)
            st.success('贴文已发布! ')
        
        