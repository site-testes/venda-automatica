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
    
    st.caption(f"Versão da Lib Google: {genai.__version__}")
    
    # DIAGNÓSTICO
    if st.button("🔍 Diagnóstico de Erro"):
        if not api_key:
            st.error("Coloque a API Key primeiro.")
        else:
            try:
                genai.configure(api_key=api_key)
                st.write("Modelos Disponíveis para sua Chave:")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        st.code(m.name)
            except Exception as e:
                st.error(f"Erro ao listar modelos: {e}")

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
            
            # TENTATIVA DE MODELOS (Fallback Robusto)
            model = None
            errors = []
            
            # Lista de modelos para tentar (do mais novo para o mais antigo)
            models_to_try = [
                'gemini-1.5-flash',
                'gemini-1.5-flash-latest',
                'gemini-1.5-pro',
                'gemini-pro-vision' # Modelo antigo que aceita imagem
            ]
            
            for m_name in models_to_try:
                try:
                    # Teste rápido de inicialização
                    model = genai.GenerativeModel(m_name)
                    break # Se não der erro na instanciação, usa esse (o erro real vem no generate, mas vamos tentar)
                except:
                    continue
            
            # Se não instanciou nenhum, volta pro padrão
            if not model:
                 model = genai.GenerativeModel('gemini-1.5-flash')

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
                # Tenta gerar. Se falhar, tenta o próximo modelo da lista manualmente
                try:
                    response = model.generate_content([prompt, image_painel, image_cupom])
                    st.code(response.text, language='markdown')
                except Exception as e:
                    # Se falhar no generate, tenta o fallback final: gemini-pro-vision
                    st.warning(f"Tentativa com modelo principal falhou: {e}. Tentando modelo de backup...")
                    model_backup = genai.GenerativeModel('gemini-pro-vision')
                    response = model_backup.generate_content([prompt, image_painel, image_cupom])
                    st.code(response.text, language='markdown')

        except Exception as e:
            st.error(f"Erro Fatal: {e}")
            st.warning("Use o botão de Diagnóstico na barra lateral para ver quais modelos sua chave aceita.")
