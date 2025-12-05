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

# Sidebar Minimalista
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("API Key", type="password")
    
    # DEBUG: Mostrar versão da biblioteca
    st.caption(f"Versão da Lib Google: {genai.__version__}")
    st.caption("Se for menor que 0.7.2, o erro vai continuar.")

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
    if not api_key:
        st.error("API Key necessária.")
    elif not uploaded_file_painel or not uploaded_file_cupom:
        st.error("Imagens necessárias.")
    elif not meta_dia:
        st.error("Meta necessária.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # TENTATIVA DE MODELOS (Fallback)
            model_name = 'gemini-1.5-flash'
            try:
                model = genai.GenerativeModel(model_name)
            except:
                model_name = 'gemini-1.5-flash-001' # Tenta versão específica
                model = genai.GenerativeModel(model_name)
            
            # Se ainda der erro, o try/except principal pega
            
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
            
            with st.spinner(f'Gerando com modelo {model_name}...'):
                response = model.generate_content([prompt, image_painel, image_cupom])
                st.code(response.text, language='markdown')

        except Exception as e:
            st.error(f"Erro Fatal: {e}")
            st.warning("Dica: Verifique se sua API Key está correta e se o arquivo requirements.txt no GitHub tem 'google-generativeai>=0.7.2'")
