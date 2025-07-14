# isso para rodar:
# python -m streamlit run app.py
import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import plotly.express as px
import json  # você esqueceu isso
from shapely.geometry import mapping, Polygon, MultiPolygon


st.set_page_config(page_title="App de Dados Habitacionais", layout="wide")
st.title("🏠 Melhorias Habitacionais")
# ========= LOGIN =========
SENHA_CORRETA = "seplan123"
senha = st.text_input("🔒 Digite a senha para acessar:", type="password")
if senha != SENHA_CORRETA:
    if senha != "":
        st.error("🚫 Senha incorreta.")
    st.stop()
    
# Cacheando leitura
@st.cache_data
def carregar_dados():
    return pd.read_feather("dados.feather")

def format_brasil(valor):
    return f"{int(valor):,}".replace(",", ".")
# Carrega dados
df = carregar_dados()
# Carrega a segunda base
df_setores = pd.read_feather("setor-censitario.feather")
#gdf_setores = gpd.read_file("Setores 2022/PE_setores_CD2022.shp")
gdf_setores = gpd.read_file("mapa_simplificado.geojson")

# Faz o merge com a base principal
df = df.merge(df_setores, on="CD_SETOR", how="left")
df = df.merge(gdf_setores, on="CD_SETOR", how="left")

# Substitui vírgulas por ponto
df["latitude"] = df["latitude"].astype(str).str.replace(",", ".")
df["longitude"] = df["longitude"].astype(str).str.replace(",", ".")

# Mostrar base de dados
mostrar_analise = st.sidebar.checkbox("📝 Análise descritiva",
value=True)
st.sidebar.text("Remova o ✅ para retirar a análise descritiva")
st.sidebar.header("Análise de variáveis")
avaliar_bairros = st.sidebar.checkbox("📍 Selecionar bairros", value=False)
setor_selecionar = st.sidebar.checkbox("💺 Selecionar Setor Censitário", value=False)
condicoes = st.sidebar.checkbox("🧐 Análise de casos")

if mostrar_analise:
    st.header("📊 Análise descritiva")
    #st.write(df)

    total_pessoas = df["qtdpessoas"].sum()

    #st.write(df["qtdpessoas"].sum())
    casas_com_banheiro = df["sem_banheiro"].apply(lambda x: 1 if x == 0 else 0).sum()
    casas_com_cimento = df["piso_cimento"].apply(lambda x: 0 if x == 1 else 1).sum()
    casas_com_revestimento = df["sem_revestimento"].apply(lambda x: 1 if x == 0 else 0).sum()
    total_mulheres = df["qtdmulheres"].sum()
    total_favelas = df["nome_favela"].dropna().nunique()
    total_idosos = df["qtd_idoso"].sum()
    total_criancas = df["qtd_primeira_infancia"].sum()
    total_pcd = df["qtd_pcd"].sum()

    st.markdown(
    f"""
        <div style="display: flex; gap: 20px; margin-top: 20px;">
        <div style="flex: 1; padding: 20px; background-color: #e0f7fa; border-radius: 10px; text-align: center;">
            <h4>👥 Total de pessoas</h4>
            <h2>{format_brasil(total_pessoas)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #f1f8e9; border-radius: 10px; text-align: center;">
            <h4>🚻 Casas com banheiro</h4>
            <h2>{format_brasil(casas_com_banheiro)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #d1d1e0; border-radius: 10px; text-align: center;">
            <h4>🧱 Casas com cimento</h4>
            <h2>{format_brasil(casas_com_cimento)}</h2>
        </div>
        </div>

        <div style="display: flex; gap: 20px; margin-top: 20px;">
        <div style="flex: 1; padding: 20px; background-color: #fce4ec; border-radius: 10px; text-align: center;">
            <h4>👩 Mulheres</h4>
            <h2>{format_brasil(total_mulheres)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #ffe0b2; border-radius: 10px; text-align: center;">
            <h4>🌆 Favelas</h4>
            <h2>{format_brasil(total_favelas)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #fff3e0; border-radius: 10px; text-align: center;">
            <h4>🏺 Casas com revestimento</h4>
            <h2>{format_brasil(casas_com_revestimento)}</h2>
        </div>
        </div>

        <div style="display: flex; gap: 20px; margin-top: 20px;">
        <div style="flex: 1; padding: 20px; background-color: #ede7f6; border-radius: 10px; text-align: center;">
            <h4>👵 Idosos</h4>
            <h2>{format_brasil(total_idosos)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #c8e6c9; border-radius: 10px; text-align: center;">
            <h4>🧒 Crianças (primeira infância)</h4>
            <h2>{format_brasil(total_criancas)}</h2>
        </div>
        <div style="flex: 1; padding: 20px; background-color: #ffe082; border-radius: 10px; text-align: center;">
            <h4>♿ PCD</h4>
            <h2>{format_brasil(total_pcd)}</h2>
        </div>
        </div>
        """,
            unsafe_allow_html=True
        )

    st.header("💰 Renda Familiar")
    df["rendafampc_valor"] = pd.to_numeric(df["rendafampc_valor"], errors="coerce")
    df_renda = df.dropna(subset=["rendafampc_valor"])
    fig = px.histogram(
    df_renda,
        x="rendafampc_valor",
        nbins=50,
        title="Distribuição da Renda Familiar Per Capita",
        labels={"rendafampc_valor": "Renda Familiar Per Capita (R$)",
        "count": "Número de famílias"}
    )

    fig.update_layout(bargap=0.1)
    fig.update_yaxes(title_text="Número de Famílias")



    st.plotly_chart(fig, use_container_width=True)
    renda_mediana = df_renda["rendafampc_valor"].median()
    renda_media = df_renda["rendafampc_valor"].mean()
    renda_min = df_renda["rendafampc_valor"].min()
    renda_max = df_renda["rendafampc_valor"].max()

    st.markdown(f"""
    > O histograma acima mostra a distribuição da renda familiar per capita das famílias cadastradas.
    > A mediana da renda é aproximadamente R\\$ {renda_mediana:,.2f}, enquanto a média é de cerca de R\\$ {renda_media:,.2f}.
    > Os valores variam entre um mínimo de R\\$ {renda_min:,.2f} e um máximo de R\\$ {renda_max:,.2f}.
    """, unsafe_allow_html=True)

    # Exibição
    st.subheader("🌍 Índice de Desenvolvimento Humano (IDH)")
    idh_medio = df["IDH"].mean()
    if idh_medio < 0.400:
        cor = "#e53935"  # vermelho
        nivel = "IDH Baixo"
    elif idh_medio < 0.600:
        cor = "#fdd835"  # amarelo
        nivel = "IDH Médio"
    else:
        cor = "#43a047"  # verde
        nivel = "IDH Alto"
        #st.markdown("#### 🧭 Índice de Desenvolvimento Humano (IDH)")
    st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <div style="width: 20px; height: 20px; background-color: {cor}; border-radius: 50%;"></div>
        <span style="font-weight: bold;">{nivel} ({idh_medio:.3f})</span>
    </div>
    """,
    unsafe_allow_html=True
)
    # garante que não haja NaN
    df_idh = df.dropna(subset=["IDH"])

    fig = px.histogram(
    df_idh,
    x="IDH",
    nbins=30,
    title="📊 Distribuição do IDH",
    labels={"IDH": "Índice de Desenvolvimento Humano (IDH)"},)

    fig.update_layout(
        xaxis_title="IDH",
        yaxis_title="Número de Regiões/Famílias",
        bargap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
    idh_mediana = df_idh["IDH"].median()
    idh_media = df_idh["IDH"].mean()
    idh_min = df_idh["IDH"].min()
    idh_max = df_idh["IDH"].max()

    st.markdown(f"""
        > O histograma acima apresenta a distribuição dos valores do Índice de Desenvolvimento Humano (IDH) entre as unidades analisadas.
        > A **mediana** do IDH é de aproximadamente **{idh_mediana:.3f}**, enquanto a **média** é de cerca de **{idh_media:.3f}**.
        > Os valores variam entre um mínimo de **{idh_min:.3f}** e um máximo de **{idh_max:.3f}**.
        """ , unsafe_allow_html=True)

    st.info("""
            O Índice de Desenvolvimento Humano (IDH) é usado para indicar o nível de desenvolvimento dos setores censitários do bairro. A classificação utilizada é:

            🔴 IDH Baixo: menor que 0,400

            🟡 IDH Médio: de 0,400 a 0,599

            🟢 IDH Alto: 0,600 ou mais

            O valor mostrado corresponde à média dos setores censitários.""")

    st.header("🗺️ Mapa de Localizações")
    st.subheader("Onde estão as famílias?")
    if {"latitude", "longitude"}.issubset(df.columns):
        # Garante que são numéricos
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        # Recife e proximidades
        df = df[
            (df["latitude"].between(-9, -7)) &
            (df["longitude"].between(-36, -34))
        ]

        #st.write(df[['latitude', 'longitude']].describe())


        # Usa apenas as colunas necessárias
        colunas_mapa = ["latitude", "longitude"]
        if "endereco_2" in df.columns:
            colunas_mapa.append("endereco_2")

        mapa_df = df[colunas_mapa].dropna(subset=["latitude", "longitude"]).copy()

        # Mostra quantos pontos válidos existem
        st.write(f"🔢 Total de pontos no mapa: {len(mapa_df)}")

        # Configura a camada do mapa
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=mapa_df,
            get_position='[longitude, latitude]',
            get_color='[0, 102, 204, 160]',
            get_radius=50,
            pickable=True,
        )

        # Tooltip com endereço (passar o mouse no mapa e aparecer)
        tooltip = {
            "html": "<b>Endereço:</b> {endereco_2}" if "endereco_2" in mapa_df.columns else "Ponto",
            "style": {"color": "white"}
        }

        # Centraliza o mapa na média das coordenadas
        view_state = pdk.ViewState(
            latitude=mapa_df["latitude"].mean(),
            longitude=mapa_df["longitude"].mean(),
            zoom=11,
            pitch=0,
        )

        # Renderiza o mapa
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=None  # usa base OpenStreetMap
        ))


    else:#aqui se houver erro (ate agora nao deu)
        st.error("Colunas 'latitude' e 'longitude' não encontradas.")
    st.header("🥇 Ranking")
    if "Bairro" not in df.columns:
        st.error("Sua base precisa ter uma coluna chamada 'Bairro'!")
        st.stop()

        # ===============================
        # 📝 Seleção da variável
        # ===============================
    variavel = st.selectbox(
        "Escolha a variável para o ranking",
        options=["Selecione uma variável", "IDH", "Quantidade de pessoas", "Índice de vulnerabilidade", "Quantidade de mulheres",
        "Quantidade de idosos", "Quantidade de crianças (primeira infância)", "Quantidade de PCDs"],
        index=0
    )
    #st.write(df)

        # ===============================
        # 📊 Agrupa e calcula
        # ===============================
    if variavel == "Selecione uma variável":
        st.warning("Por favor, escolha uma variável para ver o ranking.")
        #st.stop()
    elif variavel == "Quantidade de pessoas":
        ranking = (
        df.groupby("Bairro")["qtdpessoas"]
        .sum()
        .reset_index()
        .rename(columns={"qtdpessoas": "total"})
        .sort_values(by="total", ascending=False))

    elif variavel == "Índice de vulnerabilidade":
        ranking = (
            df.groupby("Bairro")["index"]
            .mean()
            .reset_index()
            .rename(columns={"index": "total"})
            .sort_values(by="total", ascending=False)
        )
    elif variavel =="Quantidade de mulheres":
        ranking = (
        df.groupby("Bairro")["qtdmulheres"]
        .sum()
        .reset_index()
        .rename(columns={"qtdmulheres": "total"})
        .sort_values(by="total", ascending=False)
        )
    elif variavel == "Quantidade de idosos":
        ranking = (
        df.groupby("Bairro")["qtd_idoso"]
        .sum()
        .reset_index()
        .rename(columns={"qtd_idoso": "total"})
        .sort_values(by="total", ascending=False)
        )
    elif variavel == "Quantidade de crianças (primeira infância)":
        ranking = (
        df.groupby("Bairro")["qtd_primeira_infancia"]
        .sum()
        .reset_index()
        .rename(columns={"qtd_primeira_infancia": "total"})
        .sort_values(by="total", ascending=False)
        )
    elif variavel == "Quantidade de PCDs":
        ranking = (
        df.groupby("Bairro")["qtd_pcd"]
        .sum()
        .reset_index()
        .rename(columns={"qtd_pcd": "total"})
        .sort_values(by="total", ascending=False)
        )
    else:
        ranking = (
            df.groupby("Bairro")["IDH"]
            .mean()
            .reset_index()
            .rename(columns={"IDH": "total"})
            .sort_values(by="total", ascending=False)
        )

    # só depois decide como formatar:
    if variavel == "Quantidade de pessoas":
        ranking["total"] = ranking["total"].fillna(0).round().astype(int)
    else:
        ranking["total"] = ranking["total"].fillna(0).round(3)

        # ===============================
        # 📋 Tabela
        # ===============================
    st.subheader(f"📈 Ranking dos bairros por `{variavel}`")
    #st.dataframe(ranking)
    #st.write(df)
        # ===============================
        # 📈 Gráfico
        # ===============================
    fig = px.bar(
        ranking,
        x="total",
        y="Bairro",
        orientation="h",
        title=f"Ranking dos bairros por {variavel}",
        labels={"total": "Total", "Bairro": "Bairro"},
        height=800,
        text=ranking["total"]  # coloca os valores como texto
    )

        # ordena os bairros
    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    #if variavel == "qtdpessoas":
            # força os ticks do eixo x e o texto para inteiro
            #fig.update_traces(texttemplate='%{text:.0f}')
            #fig.update_xaxes(tickformat=',d')
        #else:
            # para IDH, pode deixar com 3 casas decimais
            #fig.update_traces(texttemplate='%{text:.3f}')
    #st.write(ranking.dtypes)

    st.plotly_chart(fig, use_container_width=True)

# selecionar bairros
if avaliar_bairros:
    st.header("📍 Avaliar bairros")
    #bairros_selecionar = st.checkbox("📍 Selecionar bairro")
    #if bairros_selecionar:
    opcoes_bairro = df["nome_bairro_setor"].dropna().unique()
    opcoes_bairro = sorted(opcoes_bairro)
    opcoes_bairro = ["Selecione um bairro"] + opcoes_bairro
    bairro_escolhido = st.selectbox("Escolha um bairro:", opcoes_bairro)
    if bairro_escolhido == "Selecione um bairro":
        st.info("aguardando seleção...")
    else:
        if bairro_escolhido:
            st.success(f"✅ Bairro selecionado: {bairro_escolhido}")
            df_filtrado = df[df["nome_bairro_setor"] == bairro_escolhido]
            #st.write(df_filtrado)
            #calculos
            total_pessoas = df_filtrado["qtdpessoas"].sum()
            casas_com_banheiro = df_filtrado["sem_banheiro"].apply(lambda x: 1 if x == 0 else 0).sum()
            casas_com_cimento = df_filtrado["piso_cimento"].apply(lambda x: 0 if x == 1 else 1).sum()
            casas_com_revestimento = df_filtrado["sem_revestimento"].apply(lambda x: 1 if x == 0 else 0).sum()
            total_mulheres = df_filtrado["qtdmulheres"].sum()
            total_favelas = df_filtrado["nome_favela"].dropna().nunique()

                # Exibição
            st.subheader("📊 Indicadores do bairro")
            idh_medio = df_filtrado["IDH"].mean()
            if idh_medio < 0.400:
                cor = "#e53935"  # vermelho
                nivel = "IDH Baixo"
            elif idh_medio < 0.600:
                cor = "#fdd835"  # amarelo
                nivel = "IDH Médio"
            else:
                cor = "#43a047"  # verde
                nivel = "IDH Alto"
            st.markdown("#### 🧭 Índice de Desenvolvimento Humano (IDH)")
            st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="width: 20px; height: 20px; background-color: {cor}; border-radius: 50%;"></div>
            <span style="font-weight: bold;">{nivel} ({idh_medio:.3f})</span>
        </div>
        """,
        unsafe_allow_html=True
    )
            st.info("""
                O Índice de Desenvolvimento Humano (IDH) é usado para indicar o nível de desenvolvimento dos setores censitários do bairro. A classificação utilizada é:

                🔴 IDH Baixo: menor que 0,400

                🟡 IDH Médio: de 0,400 a 0,599

                🟢 IDH Alto: 0,600 ou mais

                O valor mostrado corresponde à média dos setores do bairro selecionado.""")


                #col1, col2, col3 = st.columns(3)
                #col1.metric("👥 Total de pessoas", f"{int(total_pessoas):,}")
                #col2.metric("🚻 Casas com banheiro", f"{int(casas_com_banheiro):,}")
                #col3.metric("👩 Mulheres", f"{int(total_mulheres):,}")
            total_registros = len(df_filtrado)
            st.markdown(
        f"""
        <div style="display: flex; gap: 20px; margin-top: 20px;">
            <div style="flex: 1; padding: 20px; background-color: #e0f7fa; border-radius: 10px; text-align: center;">
                <h4>👥 Total de pessoas</h4>
                <h2>{format_brasil(total_pessoas)}</h2>
            </div>
            <div style="flex: 1; padding: 20px; background-color: #f1f8e9; border-radius: 10px; text-align: center;">
                <h4>🚻 Casas com banheiro</h4>
                <h2>{format_brasil(casas_com_banheiro)}</h2>
            </div>
            <div style="flex: 1; padding: 20px; background-color: #d1d1e0; border-radius: 10px; text-align: center;">
                <h4>🧱 Casas com cimento</h4>
                <h2>{format_brasil(casas_com_cimento)}</h2>
            </div>
        </div>

        <div style="display: flex; gap: 20px; margin-top: 20px;">
            <div style="flex: 1; padding: 20px; background-color: #fce4ec; border-radius: 10px; text-align: center;">
                <h4>👩 Mulheres</h4>
                <h2>{format_brasil(total_mulheres)}</h2>
            </div>
            <div style="flex: 1; padding: 20px; background-color: #ffe0b2; border-radius: 10px; text-align: center;">
                <h4>🌆 Favelas</h4>
                <h2>{format_brasil(total_favelas)}</h2>
            </div>
            <div style="flex: 1; padding: 20px; background-color: #fff3e0; border-radius: 10px; text-align: center;">
                <h4>🏺 Casas com revestimento</h4>
                <h2>{format_brasil(casas_com_revestimento)}</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
        st.warning(f"🗂️ Total de registros do bairro {bairro_escolhido}: {format_brasil(total_registros)}")
        # Mapa só do bairro selecionado
        st.subheader(f"🗺️ Mapa dos locais no bairro {bairro_escolhido}")

        df_filtrado["latitude"] = pd.to_numeric(df_filtrado["latitude"].astype(str).str.replace(",", "."), errors="coerce")
        df_filtrado["longitude"] = pd.to_numeric(df_filtrado["longitude"].astype(str).str.replace(",", "."), errors="coerce")

        mapa_bairro = df_filtrado[["latitude", "longitude", "endereco_2"]].dropna(subset=["latitude", "longitude"]).copy()

        if not mapa_bairro.empty:
            layer_bairro = pdk.Layer(
                "ScatterplotLayer",
                data=mapa_bairro,
                get_position='[longitude, latitude]',
                get_color='[255, 100, 100, 160]',  # vermelho clarinho
                get_radius=30,
                pickable=True,
    )

            tooltip_bairro = {
                "html": "<b>Endereço:</b> {endereco_2}",
                "style": {"color": "white"}
    }

            view_state_bairro = pdk.ViewState(
                latitude=mapa_bairro["latitude"].mean(),
                longitude=mapa_bairro["longitude"].mean(),
                zoom=13,
                pitch=0,
    )

            st.pydeck_chart(pdk.Deck(
                layers=[layer_bairro],
                initial_view_state=view_state_bairro,
                tooltip=tooltip_bairro,
                map_style=None
    ))
        else:
            st.warning("Este bairro não possui coordenadas válidas para o mapa.")

# setor censitário
if setor_selecionar:
    st.header("💺Avaliar por Setor Censitário")
    opcoes_setor = df["CD_SETOR"].dropna().unique()
    opcoes_setor = sorted(opcoes_setor)
    opcoes_setor = ["Selecione um setor censitário"] + opcoes_setor
    setor_escolhido = st.selectbox("Escolha um setor censitário:", opcoes_setor)
    if setor_escolhido == "Selecione um setor censitário":
        st.info("aguardando seleção...")
    else:
        if setor_escolhido:
            st.success(f"✅ Setor censitário selecionado: {setor_escolhido}")
            setor_geo = df[df["CD_SETOR"] == setor_escolhido]

    # Verifica se tem geometria válida
        if "geometry" in setor_geo.columns and not setor_geo["geometry"].isna().all():
            from shapely.geometry import mapping

        # Pega a primeira geometria
            geometria = setor_geo["geometry"].dropna().iloc[0]
            coords = mapping(geometria)["coordinates"]

        # pydeck espera lista de polígonos
            polygon_layer = pdk.Layer(
                "PolygonLayer",
                data=[{"coordinates": coords}],
                get_polygon="coordinates",
                get_fill_color="[0, 150, 0, 100]",  # verde translúcido
                pickable=True,
        )

            view_state_setor = pdk.ViewState(
                latitude=geometria.centroid.y,
                longitude=geometria.centroid.x,
                zoom=14,
                pitch=0
        )

            st.subheader("🗺️ Mapa do setor censitário selecionado")
            st.pydeck_chart(pdk.Deck(
                layers=[polygon_layer],
                initial_view_state=view_state_setor,
                map_style=None
        ))
        else:
            st.warning("Este setor censitário não possui geometria disponível.")
# Análise de casos com filtros
# Formulário de análise
if condicoes:
    st.header("🧐 Análise de casos")
    with st.form("formulario_familias"):
        inserir_familias = st.number_input(
            "Digite a quantidade de famílias",
            min_value=1,
            max_value=None,
            step=1,
            format="%d"
        )

        st.markdown("### \U0001F4B0 Filtrar por Renda Familiar Per Capita")
        df["rendafampc_valor"] = pd.to_numeric(df["rendafampc_valor"], errors="coerce")
        renda_max = float(df["rendafampc_valor"].max())
        faixa_renda = st.slider("Selecione a faixa de renda (R$)", 0.0, renda_max, (0.0, renda_max), step=1.0)

        st.markdown("### \U0001F4B5 Avaliação de custo")
        df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce")
        custo_max = float(df["custo_total"].max())
        faixa_custo = st.slider("Selecione o custo (R$)", 0.0, custo_max, (0.0, custo_max), step=1.0)

        submitted = st.form_submit_button("Confirmar")

    if submitted:
        if 1 <= inserir_familias <= len(df):
            df_filtrado = df[
                (df["rendafampc_valor"] >= faixa_renda[0]) &
                (df["rendafampc_valor"] <= faixa_renda[1]) &
                (df["custo_total"] >= faixa_custo[0]) &
                (df["custo_total"] <= faixa_custo[1])
            ]

            df_vulneraveis = df_filtrado.sort_values(by="index", ascending=False).head(inserir_familias).copy()

            if not df_vulneraveis.empty:
                st.success(f"Você selecionou {len(df_vulneraveis)} famílias mais vulneráveis.")
                st.session_state["df_filtrado_resultado"] = df_vulneraveis.reset_index(drop=True)
                st.session_state["num_familias_filtradas"] = inserir_familias
            else:
                st.warning("Nenhuma família encontrada com os filtros selecionados.")
        else:
            st.error(f"O valor deve ser entre 1 e {len(df)}.")

    # Resultado (mapa e tabela)
    if "df_filtrado_resultado" in st.session_state:
        df_vulneraveis = st.session_state["df_filtrado_resultado"]
        setores_vulneraveis = df_vulneraveis["CD_SETOR"].dropna().unique()
        setores_df = df[df["CD_SETOR"].isin(setores_vulneraveis) & df["geometry"].notna()].drop_duplicates("CD_SETOR")

        if not setores_df.empty:
            polygons = []
            for _, row in setores_df.iterrows():
                geometria = row["geometry"]
                if isinstance(geometria, (Polygon, MultiPolygon)):
                    coords_raw = mapping(geometria)["coordinates"]
                    coords_list = [poly[0] for poly in coords_raw] if isinstance(geometria, MultiPolygon) else [coords_raw[0]]
                    for coords in coords_list:
                        polygons.append({
                            "coordinates": [coords],
                            "setor": row["CD_SETOR"],
                            "bairro": row["nome_bairro_setor"]
                        })

            layer = pdk.Layer(
                "PolygonLayer",
                data=polygons,
                get_polygon="coordinates",
                get_fill_color="[255, 0, 0, 80]",
                get_line_color="[0, 0, 0]",
                get_line_width=1,
                pickable=True
            )

            tooltip = {
                "html": "<b>Bairro:</b> {bairro}<br><b>Setor:</b> {setor}",
                "style": {"color": "white", "backgroundColor": "#2c3e50", "padding": "10px", "borderRadius": "5px"}
            }

            centro = setores_df.iloc[0]["geometry"].centroid
            view_state = pdk.ViewState(latitude=centro.y, longitude=centro.x, zoom=13, pitch=0)

            st.subheader("\U0001F5FA\ufe0f Setores das famílias mais vulneráveis")
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style=None))

        mostrar_tabela = st.checkbox(f"\U0001F4CB Visualizar tabela com {st.session_state.get('num_familias_filtradas', '?')} famílias filtradas")
        if mostrar_tabela:
            st.dataframe(df_vulneraveis)
