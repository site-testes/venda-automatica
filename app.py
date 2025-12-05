import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da Página
st.set_page_config(
    page_title="Gerador de Relatório BK",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Customizado (Opcional, para dar um toque mais 'clean')
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF8732;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #E06000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar para Configurações
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Burger_King_logo_%281999%29.svg/2024px-Burger_King_logo_%281999%29.svg.png", width=100)
    st.title("Configurações")
    api_key = st.text_input("🔑 Google API Key", type="password", help="Insira sua chave da API do Google Gemini aqui.")
    st.markdown("---")
    st.markdown("**Como usar:**")
    st.markdown("1. Insira sua API Key.")
    st.markdown("2. Digite a Meta do Dia.")
    st.markdown("3. Envie as fotos do Painel e do Cupom.")
    st.markdown("4. Clique em 'Gerar Relatório'.")

# Cabeçalho Principal
st.title("🍔 Gerador de Relatório BK - Automático")
st.markdown("### Transforme suas fotos em relatório de vendas em segundos.")
st.markdown("---")

# Layout em Colunas para Inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Dados do Dia")
    meta_dia = st.text_input("💰 Meta do Dia (R$)", placeholder="Ex: 25000.00")

with col2:
    st.subheader("2️⃣ Upload das Fotos")
    uploaded_file_painel = st.file_uploader("📸 Foto do Painel de Metas", type=["jpg", "png", "jpeg"])
    uploaded_file_cupom = st.file_uploader("🧾 Foto do Cupom Fiscal", type=["jpg", "png", "jpeg"])

st.markdown("---")

# Botão de Ação
st.subheader("3️⃣ Gerar Relatório")
if st.button("🚀 Processar e Gerar Relatório"):
    if not api_key:
        st.warning("⚠️ Por favor, insira a Google API Key na barra lateral.")
    elif not uploaded_file_painel or not uploaded_file_cupom:
        st.warning("⚠️ Por favor, faça o upload das duas imagens (Painel e Cupom).")
    elif not meta_dia:
        st.warning("⚠️ Por favor, insira o valor da Meta do Dia.")
    else:
        try:
            # Configuração da API
            genai.configure(api_key=api_key)
            
            # Carregando o Modelo
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Processando Imagens
            image_painel = Image.open(uploaded_file_painel)
            image_cupom = Image.open(uploaded_file_cupom)
            
            # Prompt do Sistema (Mantido igual)
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
            
            with st.spinner('🤖 A IA está analisando suas fotos... Aguarde um momento.'):
                response = model.generate_content([prompt, image_painel, image_cupom])
                
                st.success("✅ Relatório Gerado com Sucesso!")
                st.markdown("### 📋 Resultado:")
                st.code(response.text, language='markdown')
                st.info("💡 Dica: Clique no ícone de copiar no canto superior direito do bloco de código acima para colar no WhatsApp.")

        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao gerar o relatório: {e}")
