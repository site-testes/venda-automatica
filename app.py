import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da Página
st.set_page_config(
    page_title="Relatório BK",
    page_icon="🍔",
    layout="wide"
)

# CSS para visual limpo e responsivo
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #d62300; /* Vermelho BK */
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background-color: #b51d00;
        color: white;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Esconder menu padrão do Streamlit para visual mais limpo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA API ---
# A chave está definida aqui para não precisar digitar.
# OBS: Em um projeto público real, o ideal é usar st.secrets, mas para seu uso pessoal direto no código funciona.
API_KEY = "AIzaSyDsvskF4zhNeSs8W1D499_FR89wNPdOkr8"

# Sidebar (Apenas título, sem inputs)
with st.sidebar:
    st.header("Burger King")
    st.info("Sistema Automático de Relatórios")

# Layout Principal
st.title("Relatório de Vendas")

# Container para Inputs (Responsivo: em mobile fica um abaixo do outro)
with st.container():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        meta_dia = st.text_input("Meta do Dia (R$)", placeholder="0.00")
    
    with col2:
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            uploaded_file_painel = st.file_uploader("Painel de Metas", type=["jpg", "png", "jpeg"])
        with col_up2:
            uploaded_file_cupom = st.file_uploader("Cupom Fiscal", type=["jpg", "png", "jpeg"])

st.markdown("---")

# Botão de Ação Full Width
if st.button("PROCESSAR DADOS"):
    if not uploaded_file_painel or not uploaded_file_cupom:
        st.error("Imagens necessárias.")
    elif not meta_dia:
        st.error("Meta necessária.")
    else:
        try:
            genai.configure(api_key=API_KEY)
            
            # SELEÇÃO DINÂMICA DE MODELO
            active_model_name = None
            
            try:
                # Procura o primeiro modelo Flash ou Pro disponível na conta
                # Prioridade: Flash -> Pro -> Qualquer um
                models = genai.list_models()
                
                # 1. Tenta Flash
                for m in models:
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
                        active_model_name = m.name
                        break
                
                # 2. Tenta Pro (se não achou flash)
                if not active_model_name:
                    for m in models:
                        if 'generateContent' in m.supported_generation_methods and 'pro' in m.name.lower():
                            active_model_name = m.name
                            break
                
                # 3. Fallback genérico
                if not active_model_name:
                     for m in models:
                        if 'generateContent' in m.supported_generation_methods:
                            active_model_name = m.name
                            break
            except Exception:
                # Se falhar a listagem (ex: erro de rede), tenta o padrão hardcoded
                active_model_name = 'gemini-1.5-flash'

            if not active_model_name:
                st.error("Erro: Nenhum modelo de IA disponível na sua conta.")
                st.stop()

            model = genai.GenerativeModel(active_model_name)

            image_painel = Image.open(uploaded_file_painel)
            image_cupom = Image.open(uploaded_file_cupom)
            
            prompt = f"""
            Você é um assistente especializado em gerar relatórios de vendas do Burger King.
            
            Abaixo estão duas imagens:
            1. Foto do Painel de Metas.
            2. Foto do Cupom Fiscal.
            
            A Meta do Dia digitada pelo usuário é: {meta_dia}
            
            --- REGRAS DE NEGÓCIO ---
            1. Analise a 'Foto do Cupom Fiscal': Encontre o valor TOTAL da venda. Subtraia 13% desse valor. O resultado é o 'R' (Realizado) da Venda.
            2. Analise a 'Foto do Painel de Metas': Extraia o 'Itens Vendidos' (R) e a 'Meta' (P) de: Premium, Cupons, Kids.
            3. Extraia as porcentagens (%) de 'Combagem' e 'KingEmDobro'.
            4. Sobremesa: O 'P' (Projetado) é SEMPRE 100. O 'R' (Realizado) deve ser preenchido sempre com "???".
            5. A Saída deve ser APENAS a tabela abaixo, dentro de um bloco de código markdown, sem explicações extras.
            
            ### TEMPLATE DE SAÍDA OBRIGATÓRIO
            Drive - W.L

            [DATA ATUAL DD/MM/AAAA]

            Venda P: {meta_dia} R: [Valor do Cupom - 13%]

            Premium P: [Meta extraída da foto] R: [Realizado extraído da foto]

            cupons P: [Meta extraída da foto] R: [Realizado extraído da foto]

            kids P: [Meta extraída da foto] R: [Realizado extraído da foto]

            Combagem P: [Meta extraída da foto]% R: [Realizado extraído da foto]%

            kingemdobro P: [Meta extraída da foto]% R: [Realizado extraído da foto]%

            Sobremesa P: 100 R: ???

            Lançamentos

            Dia B ✅ D/C ✅ D/I ✅

            Noite B ✅ D/C ✅ D/I ✅

            Madrugada B ✅ D/I✅ D/C ✅ Contagem✅
            """
            
            with st.spinner(f'Gerando relatório...'):
                response = model.generate_content([prompt, image_painel, image_cupom])
                st.code(response.text, language='markdown')

        except Exception as e:
            st.error(f"Erro: {e}")
