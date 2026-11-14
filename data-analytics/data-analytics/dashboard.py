
# PHOENIX FIRE INTELLIGENCE
# Data Analytics Dashboard - English Edition

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="PHOENIX FIRE INTELLIGENCE",
    page_icon="🔥",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background-color: #0B1220;
}
[data-testid="stSidebar"] {
    background-color: #111827;
}
[data-testid="stMetric"] {
    background-color: #172033;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #28354B;
}
[data-testid="stMetricValue"] {
    color: #FF9A3C;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def read_dataset(filename, modified_time):
    return pd.read_csv(DATA_DIR / filename)


def load_dataset(filename):
    path = DATA_DIR / filename

    if not path.is_file():
        st.error(f"Missing dataset: {filename}")
        st.info(
            "Run python export_data.py to generate "
            "the required CSV files."
        )
        st.stop()

    return read_dataset(
        filename,
        path.stat().st_mtime_ns,
    )


def show_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B1220",
        plot_bgcolor="#111827",
    )
    st.plotly_chart(fig, width="stretch")


def show_table(frame):
    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
    )


def download_csv(frame, filename):
    st.download_button(
        "Download CSV",
        frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
    )


experiments = load_dataset(
    "integrated_experiments.csv"
)

evidence = load_dataset(
    "evidence_matrix.csv"
)

saffire = load_dataset(
    "saffire_classification.csv"
)

quality = load_dataset(
    "quality_flags.csv"
)

# Check exported data consistency
if (
    len(experiments) != 285
    or len(evidence) != 285
    or len(saffire) != 11
    or len(quality) != 12
    or not experiments["test_id"].is_unique
    or set(experiments["test_id"])
       != set(evidence["test_id"])
    or evidence["quality_flag_count"].sum() != 12
):
    st.error(
        "Data integrity check failed. "
        "Please verify the exported datasets."
    )
    st.stop()


st.title("🔥 PHOENIX FIRE INTELLIGENCE")
st.markdown(
    "**PHOENIX Orbit | NASA Space Apps Challenge 2026**"
)
st.caption(
    "Exploratory analysis of NASA combustion "
    "experiments under microgravity conditions."
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Integrated Tests", len(experiments))

c2.metric(
    "FLEX Tests",
    int((experiments["experiment"] == "FLEX").sum()),
)

c3.metric(
    "SAFFIRE Tests",
    int(
        experiments["experiment"]
        .str.startswith("SAFFIRE")
        .sum()
    ),
)

c4.metric(
    "Quality Flags",
    int(evidence["quality_flag_count"].sum()),
)

st.sidebar.title("PHOENIX Orbit")

page = st.sidebar.radio(
    "Data Analytics",
    [
        "Overview",
        "FLEX Analysis",
        "SAFFIRE Analysis",
        "Data Quality",
        "NASA Resources",
    ],
)

st.divider()

if page == "Overview":

    st.header("Experimental Data Overview")

    distribution = (
        experiments["experiment"]
        .value_counts()
        .rename_axis("experiment")
        .reset_index(name="tests")
    )

    show_chart(
        px.bar(
            distribution,
            x="experiment",
            y="tests",
            color="experiment",
            text="tests",
            title="Tests by Experiment",
        )
    )

    coverage = (
        evidence["data_coverage"]
        .value_counts()
        .rename_axis("coverage")
        .reset_index(name="tests")
    )

    show_chart(
        px.bar(
            coverage,
            x="coverage",
            y="tests",
            color="coverage",
            title="Selected Variable Availability",
        )
    )

    st.info(
        "Data coverage refers to variable availability. "
        "It does not establish scientific reliability "
        "or fire hazard severity."
    )

    show_table(distribution)

elif page == "FLEX Analysis":

    st.header("FLEX Droplet Combustion Analysis")

    flex = experiments[
        experiments["experiment"] == "FLEX"
    ].copy()

    fuels = sorted(
        flex["material"].dropna().unique().tolist()
    )

    selected_fuels = st.multiselect(
        "Select fuels",
        fuels,
        default=fuels,
    )

    flex = flex[
        flex["material"].isin(selected_fuels)
    ].copy()

    exclude_invalid_pressure = st.checkbox(
        "Exclude non-positive pressure values",
        value=True,
    )

    if exclude_invalid_pressure:
        flex = flex[
            pd.to_numeric(
                flex["pressure_kpa"], errors="coerce"
            ) > 0
        ].copy()

    if flex.empty:
        st.warning("No tests match the selected filters.")

    else:
        flex["burn_time_s"] = pd.to_numeric(
            flex["burn_time_s"],
            errors="coerce",
        )

        flex["oxygen_percent"] = pd.to_numeric(
            flex["oxygen_percent"],
            errors="coerce",
        )

        summary = flex.groupby("material").agg(
            tests=("test_id", "count"),
            recorded_durations=("burn_time_s", "count"),
            median_burn_time_s=("burn_time_s", "median"),
            mean_burn_time_s=("burn_time_s", "mean"),
        ).reset_index()

        st.subheader("Descriptive Statistics")
        show_table(summary.round(3))

        points = flex.dropna(
            subset=["oxygen_percent", "burn_time_s"]
        )

        if not points.empty:
            show_chart(
                px.scatter(
                    points,
                    x="oxygen_percent",
                    y="burn_time_s",
                    color="material",
                    hover_data=["test_id", "pressure_kpa"],
                    title="Oxygen and Burn Duration",
                    labels={
                        "oxygen_percent": "Oxygen (%)",
                        "burn_time_s": "Burn duration (s)",
                    },
                )
            )

            show_chart(
                px.box(
                    points,
                    x="material",
                    y="burn_time_s",
                    color="material",
                    points="all",
                    title="Burn Duration by Fuel",
                )
            )

        st.warning(
            "Observed relationships are exploratory. "
            "Oxygen concentration, pressure, droplet "
            "diameter, and experimental outcome may "
            "affect interpretation. Correlation does "
            "not establish causation or fire hazard."
        )

        show_table(flex)
        download_csv(flex, "flex_filtered.csv")

elif page == "SAFFIRE Analysis":

    st.header("SAFFIRE Solid Material Combustion")

    selected = st.multiselect(
        "Select experiments",
        ["SAFFIRE-I", "SAFFIRE-II"],
        default=["SAFFIRE-I", "SAFFIRE-II"],
    )

    selected_data = saffire[
        saffire["experiment"].isin(selected)
    ].copy()

    numeric = selected_data.dropna(
        subset=["burn_time_s"]
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Selected Tests", len(selected_data))
    c2.metric("Numeric Durations", len(numeric))
    c3.metric(
        "Qualitative Results",
        len(selected_data) - len(numeric),
    )

    if not numeric.empty:
        show_chart(
            px.bar(
                numeric,
                x="sample_id",
                y="burn_time_s",
                color="experiment",
                hover_data=["material"],
                title="Reported Burn Durations",
            )
        )

    if not selected_data.empty:
        behavior = (
            selected_data.groupby(
                ["experiment", "reported_behavior"]
            )
            .size()
            .reset_index(name="tests")
        )

        show_chart(
            px.bar(
                behavior,
                x="experiment",
                y="tests",
                color="reported_behavior",
                barmode="group",
                title="Reported Experimental Outcomes",
            )
        )

    st.info(
        "'Insignificant combustion reported' is a "
        "qualitative result, not a measured duration "
        "of zero seconds."
    )

    oxygen = experiments[
        experiments["experiment"] == "SAFFIRE-II"
    ]

    st.subheader("SAFFIRE-II Oxygen Measurements")

    show_table(
        oxygen[
            [
                "test_id",
                "oxygen_original_text",
                "oxygen_percent",
                "oxygen_min_percent",
                "oxygen_max_percent",
                "oxygen_value_type",
            ]
        ]
    )

    st.caption(
        "Interval midpoints are representative "
        "values, not exact measurements."
    )

    st.subheader("SAFFIRE Classification")
    show_table(selected_data)

    download_csv(
        selected_data,
        "saffire_filtered.csv",
    )

elif page == "Data Quality":

    st.header("Data Quality and Traceability")

    st.warning(
        "Review priority describes data issues, "
        "not fire hazard severity."
    )

    priorities = (
        evidence["review_priority"].value_counts()
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Routine Review",
        int(priorities.get("Routine", 0)),
    )

    c2.metric(
        "Medium Priority",
        int(priorities.get("Medium", 0)),
    )

    c3.metric(
        "High Priority",
        int(priorities.get("High", 0)),
    )

    grouped = (
        quality.groupby(
            ["experiment", "review_priority"]
        )
        .size()
        .reset_index(name="flags")
    )

    show_chart(
        px.bar(
            grouped,
            x="experiment",
            y="flags",
            color="review_priority",
            barmode="group",
            title="Documented Quality Flags",
        )
    )

    st.subheader("Quality Audit")
    show_table(quality)

    st.subheader("Scientific Evidence Matrix")

    selected_priority = st.multiselect(
        "Review priority",
        ["Routine", "Medium", "High"],
        default=["Routine", "Medium", "High"],
    )

    filtered = evidence[
        evidence["review_priority"].isin(
            selected_priority
        )
    ]

    show_table(filtered)

    download_csv(
        filtered,
        "evidence_matrix_filtered.csv",
    )

    st.info(
        "A test with no detected quality flags "
        "is not necessarily scientifically validated."
    )

elif page == "NASA Resources":

    st.header("NASA Scientific Resources")

    resources = {
        "NASA PSI Combustion Data":
            "https://psi.nasa.gov/physci/repo/search?q=combustion",
        "NASA Combustion Science":
            "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "NASA ScienceCasts - ISS Combustion":
            "https://www.youtube.com/watch?v=W1oXykoz9zg",
        "ISS Combustion Science Researcher's Guide":
            "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/",
        "Apollo 1":
            "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1",
        "Apollo 13":
            "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13",
        "Mir Space Station Fire":
            "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/",
        "Fireman's Air Tanks":
            "https://spinoff.nasa.gov/node/9582",
        "Fire Detector":
            "https://spinoff.nasa.gov/node/9407",
        "New Technology for the Fire Attire":
            "https://spinoff.nasa.gov/node/9918",
    }

    st.write(
        "Official NASA materials supporting "
        "experimental research, historical case "
        "studies, and fire safety technologies."
    )

    for label, url in resources.items():
        st.link_button(label, url)

    st.info(
        "Historical incidents and technology "
        "transfer examples are not included in "
        "the 285 experimental tests."
    )


st.divider()

st.caption(
    "PHOENIX FIRE INTELLIGENCE | PHOENIX Orbit | "
    "NASA Space Apps Challenge 2026"
)

st.caption(
    "Data Analytics Module | Exploratory results | "
    "Independent student project, not an official NASA product."
)
