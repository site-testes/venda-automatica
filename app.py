import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import streamlit.components.v1 as components
from dotenv import load_dotenv
from datetime import datetime

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
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stApp > header {display: none;}
    
    /* Esconder botões flutuantes inferiores (Deploy, Status, etc) */
    .stDeployButton {display:none;}
    [data-testid="stDecoration"] {display:none;}
    [data-testid="stStatusWidget"] {display:none;}
    div[class*="viewerBadge"] {display: none;}
    
    /* Forçar remoção de footer e header */
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    header {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[class^="viewerBadge"] {display: none !important;}
    
    /* Tentar esconder pelo texto ou posição se possível */
    [data-testid="stFooter"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA API ---
API_KEY = "AIzaSyDsvskF4zhNeSs8W1D499_FR89wNPdOkr8"

# Sidebar (Apenas título, sem inputs)
with st.sidebar:
    st.header("Burger King")
    st.info("Sistema Automático de Relatórios")

# Layout Principal
st.title("Relatório de Vendas")

# Container para Inputs
with st.container():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        meta_dia = st.text_input("Meta do Dia (R$)", placeholder="0.00")
    
    with col2:
        col_up1, col_up2 = st.columns(2)
        
        with col_up1:
            st.markdown("###### Painel de Metas")
            tab_cam1, tab_up1 = st.tabs(["📸 Câmera", "📂 Galeria"])
            with tab_cam1:
                img_painel_cam = st.camera_input("Foto Painel", label_visibility="collapsed")
            with tab_up1:
                img_painel_up = st.file_uploader("Upload Painel", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
            
            uploaded_file_painel = img_painel_cam if img_painel_cam else img_painel_up

        with col_up2:
            st.markdown("###### Cupom Fiscal")
            tab_cam2, tab_up2 = st.tabs(["📸 Câmera", "📂 Galeria"])
            with tab_cam2:
                img_cupom_cam = st.camera_input("Foto Cupom", label_visibility="collapsed")
            with tab_up2:
                img_cupom_up = st.file_uploader("Upload Cupom", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
            
            uploaded_file_cupom = img_cupom_cam if img_cupom_cam else img_cupom_up

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
                models = genai.list_models()
                # 1. Tenta Flash
                for m in models:
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
                        active_model_name = m.name
                        break
                # 2. Tenta Pro
                if not active_model_name:
                    for m in models:
                        if 'generateContent' in m.supported_generation_methods and 'pro' in m.name.lower():
                            active_model_name = m.name
                            break
                # 3. Fallback
                if not active_model_name:
                     for m in models:
                        if 'generateContent' in m.supported_generation_methods:
                            active_model_name = m.name
                            break
            except Exception:
                active_model_name = 'gemini-1.5-flash'

            if not active_model_name:
                st.error("Erro: Nenhum modelo de IA disponível na sua conta.")
                st.stop()

            model = genai.GenerativeModel(active_model_name)

            image_painel = Image.open(uploaded_file_painel)
            image_cupom = Image.open(uploaded_file_cupom)
            
            # Data atual formatada
            data_atual = datetime.now().strftime("%d/%m/%Y")
            
            prompt = f"""
            # Role (Papel)
            Você é um assistente especializado em auditoria de vendas do Burger King. Sua função é analisar imagens de relatórios operacionais e gerar um resumo de turno formatado para WhatsApp.

            # Inputs (Entradas)
            Você receberá:
            1. Uma imagem de um "Cupom Fiscal/Relatório de Fechamento" (fundo branco, lista de valores).
            2. Uma imagem da tela "METAS DO DIA" (fundo branco/laranja, com barras de progresso).
            3. Um valor numérico fornecido pelo usuário que representa a "Meta de Venda do Dia" (Projetado): {meta_dia}
            4. A Data de Hoje é: {data_atual}

            # Instruções de Processamento (Passo a Passo)

            ## PASSO 1: Identificação das Imagens
            Analise as duas imagens fornecidas e identifique qual é qual, independentemente da ordem de envio.
            - Imagem A (Relatório): Contém textos como "LOJA", "DRIVE", "TOTEM", "TOTAL" e valores monetários.
            - Imagem B (Metas): Contém o título "METAS DO DIA" e itens como "premium", "cupomfisico", "kids", "combagem", "kingemdobro".

            ## PASSO 2: Extração e Cálculo da Venda (Imagem A)
            1. Na Imagem A, localize a linha final ou o bloco que contém o valor "TOTAL" geral das vendas (geralmente o maior valor numérico no rodapé ou na coluna da direita).
            2. Pegue esse valor TOTAL BRUTO.
            3. APLIQUE A REGRA DE DESCONTO: Subtraia exatamente 13% desse valor total.
               - Fórmula: `Valor_Realizado = Total_Bruto - (Total_Bruto * 0.13)`
            4. Arredonde o resultado para duas casas decimais. Este será o valor "R" (Realizado) da Venda.

            ## PASSO 3: Extração dos Itens (Imagem B)
            Na Imagem B, extraia os valores numéricos para cada categoria. Atenção:
            - "P" (Projetado/Meta): É o número que aparece à direita, na coluna "Meta".
            - "R" (Realizado/Atingido): É o número que aparece dentro ou ao lado da barra colorida (laranja/verde) na coluna "Itens vendidos".
            
            **REGRA VISUAL IMPORTANTE:**
            - Se a barra de progresso ou o círculo indicador estiver na cor **CINZA** (sem preenchimento laranja/amarelo), o valor Realizado (R) é **0** (zero).
            - Exemplo: Se "kids" tem um círculo cinza, R = 0.

            Extraia os dados para:
            - Premium
            - Cupons (pode aparecer como "cupomfisico")
            - Kids
            - Combagem (Este valor é uma porcentagem %)
            - King em Dobro (Este valor é uma porcentagem %)

            ## PASSO 4: Regras Fixas (Hardcoded)
            - Para o item "Sobremesa":
              - O Projetado (P) é SEMPRE: 100
              - O Realizado (R) é SEMPRE: ??? (três interrogações).
            - O Projetado (P) da categoria "Venda" é o valor numérico fornecido pelo usuário no input de texto ({meta_dia}).

            ## PASSO 5: Formatação de Saída
            Gere a resposta APENAS com o bloco de código abaixo, sem adicionar introduções ou conclusões. Mantenha a formatação exata para que o alinhamento funcione no WhatsApp (bloco de código).
            
            ### TEMPLATE DE SAÍDA OBRIGATÓRIO
            *Drive - W.L*

            {data_atual}

            *Venda*
            P: {meta_dia}
            R: [Valor Calculado no Passo 2]

            *cupons*
            P: [Meta extraída]
            R: [Realizado extraído]

            *Premium*
            P: [Meta extraída]
            R: [Realizado extraído]

            *kids*
            P: [Meta extraída]
            R: [Realizado extraído]

            *Combagem*
            P: [Meta extraída]%
            R: [Realizado extraído]%

            *kingemdobro*
            P: [Meta extraída]%
            R: [Realizado extraído]%

            *Sobremesa*
            P: 100
            R: ???

            *Lançamentos*

            *Dia*
            B ✅
            D/C ✅
            D/I ✅

            *Noite*
            B ✅
            D/C ✅
            D/I ✅

            *Madrugada*
            B ✅
            D/I✅
            D/C ✅
            Contagem✅
            """
            
            with st.spinner(f'Gerando relatório...'):
                response = model.generate_content([prompt, image_painel, image_cupom])
                # Limpeza do texto: remove os blocos de código markdown (```)
                text_output = response.text.replace('```markdown', '').replace('```', '').strip()
                
                st.code(text_output, language='markdown')
                
                # Botão de Copiar Customizado (HTML/JS)
                # Escapando caracteres para evitar quebra do JS
                js_text = text_output.replace('`', '\\`').replace('$', '\\$').replace('\\n', '\\\\n').replace("'", "\\'")
                
                components.html(
                    f"""
                    <style>
                        .copy-btn {{
                            width: 100%;
                            background-color: #d62300;
                            color: white;
                            border-radius: 8px;
                            height: 50px;
                            font-weight: 600;
                            border: none;
                            cursor: pointer;
                            font-family: "Source Sans Pro", sans-serif;
                            font-size: 16px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                        .copy-btn:hover {{
                            background-color: #b51d00;
                        }}
                        .copy-btn:active {{
                            background-color: #901700;
                        }}
                    </style>
                    <button class="copy-btn" onclick="copyToClipboard()">📋 COPIAR RELATÓRIO</button>
                    <script>
                        function copyToClipboard() {{
                            const text = `{js_text}`;
                            navigator.clipboard.writeText(text).then(function() {{
                                const btn = document.querySelector('.copy-btn');
                                btn.innerText = '✅ COPIADO!';
                                setTimeout(() => {{ btn.innerText = '📋 COPIAR RELATÓRIO'; }}, 2000);
                            }}, function(err) {{
                                console.error('Erro ao copiar: ', err);
                                alert('Erro ao copiar. Tente selecionar manualmente.');
                            }});
                        }}
                        
                        // Auto-scroll mais agressivo
                        function scrollToBottom() {{
                            try {{
                                // Tenta rolar o elemento HTML principal do pai
                                window.parent.document.documentElement.scrollTop = 999999;
                                // Tenta rolar o corpo do pai
                                window.parent.document.body.scrollTop = 999999;
                                // Tenta o método padrão de janela
                                window.parent.window.scrollTo(0, 999999);
                            }} catch (e) {{
                                console.log("Erro no auto-scroll:", e);
                            }}
                        }}
                        
                        // Executa várias vezes para garantir
                        setTimeout(scrollToBottom, 100);
                        setTimeout(scrollToBottom, 500);
                        setTimeout(scrollToBottom, 1000);
                    </script>
                    """,
                    height=60
                )

        except Exception as e:
            st.error(f"Erro: {e}")
