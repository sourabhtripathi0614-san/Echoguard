import streamlit as st
import numpy as np
import json
from datetime import datetime
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.clip_service import CLIPService
from qdrant_service_fixed import QdrantService
from backend.memory_service import MemoryService
from config_fixed import CRISIS_PROTOCOLS, SYNTHETIC_CRISES

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="EchoGuard - Crisis Response System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { padding: 20px; }
    .crisis-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .success { color: #00d084; font-weight: bold; }
    .error { color: #ff6b6b; font-weight: bold; }
    .warning { color: #ffa502; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZE SERVICES
# ============================================================
@st.cache_resource
def initialize_services():
    """Initialize all services ONCE"""
    print("\n" + "="*70)
    print("🚀 INITIALIZING ECHOGUARD SYSTEM - FIXED VERSION")
    print("="*70 + "\n")

    # 1. Initialize Qdrant
    print("📍 Initializing Qdrant...")
    qdrant_svc = QdrantService()
    qdrant_svc.create_collection()
    print("✅ Qdrant initialized\n")

    # 2. Initialize CLIP
    print("📍 Loading CLIP model...")
    clip_service = CLIPService()
    print("✅ CLIP model loaded\n")

    # 3. Initialize Memory
    print("📍 Initializing memory service...")
    memory_service = MemoryService()
    print("✅ Memory service initialized\n")

    # 4. Load synthetic crisis data with REAL EMBEDDINGS
    print("📍 Generating embeddings for 25 REAL crisis cases...")
    vectors = []
    
    for idx, crisis in enumerate(SYNTHETIC_CRISES):
        # Generate real text embedding from description and type
        text_for_embedding = f"{crisis['type']}: {crisis['location']} - {crisis['description']}"
        embedding = clip_service.generate_text_embedding(text_for_embedding)
        vectors.append(embedding.tolist())
        
        if (idx + 1) % 5 == 0:
            print(f"  ✅ Generated embeddings for {idx + 1}/{len(SYNTHETIC_CRISES)} crises")

    # Load into Qdrant
    qdrant_svc.initialize_with_synthetic_data(vectors)

    print("="*70)
    print("✅ SYSTEM INITIALIZATION COMPLETE - ALL SERVICES READY")
    print("="*70 + "\n")

    return qdrant_svc, clip_service, memory_service

# Initialize
qdrant_service, clip_service, memory_service = initialize_services()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h1>🚨 EchoGuard - Multimodal Crisis Response System</h1>
    <p style="font-size: 18px; color: #666;">AI-powered disaster intelligence using image + text analysis</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN INTERFACE
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Analyze Crisis",
    "📊 View Database",
    "📚 Past Incidents",
    "ℹ️ Info"
])

# ============ TAB 1: ANALYZE CRISIS ============
with tab1:
    st.markdown("### Upload Crisis Image & Description")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📷 Upload Image**")
        uploaded_image = st.file_uploader(
            "Choose an image of the crisis",
            type=["jpg", "jpeg", "png", "bmp", "webp"]
        )

        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Crisis Image", width=300)

    with col2:
        st.markdown("**📝 Crisis Description**")
        crisis_description = st.text_area(
            "Describe the crisis situation",
            placeholder="e.g., Heavy flooding in residential area, 5000 people affected...",
            height=150
        )

        crisis_type = st.selectbox(
            "Crisis Type (for reference)",
            ["flood", "fire", "earthquake", "landslide", "cyclone"]
        )

        severity = st.select_slider(
            "Severity Level",
            options=["info", "low", "medium", "high", "critical"],
            value="high"
        )

    # ============ ANALYZE BUTTON ============
    if st.button("🔍 Analyze Crisis & Search Database", use_container_width=True, key="analyze"):
        if not uploaded_image or not crisis_description:
            st.error("❌ Please upload image AND provide description")
        else:
            with st.spinner("🔄 Processing crisis analysis..."):
                try:
                    # Step 1: Generate image embedding
                    st.info("📊 Step 1/4: Generating image embedding...")
                    image_embedding = clip_service.generate_image_embedding(uploaded_image)

                    # Step 2: Generate text embedding
                    st.info("📊 Step 2/4: Generating text embedding...")
                    text_embedding = clip_service.generate_text_embedding(crisis_description)

                    # Step 3: Create hybrid embedding (60% image, 40% text)
                    st.info("📊 Step 3/4: Creating hybrid multimodal embedding...")
                    hybrid_embedding = clip_service.generate_hybrid_embedding(
                        image_embedding,
                        text_embedding,
                        image_weight=0.6
                    )

                    # Step 4: Search Qdrant database
                    st.info("📊 Step 4/4: Searching for similar past incidents...")
                    similar_crises = qdrant_service.search_similar(
                        hybrid_embedding,
                        top_k=3,
                        min_score=0.0
                    )

                    # Apply temporal decay
                    similar_crises = qdrant_service.apply_temporal_decay(similar_crises)

                    st.success("✅ Analysis Complete!")

                    # ============ DISPLAY RESULTS ============
                    st.markdown("### 📊 Analysis Results")

                    # Show found incidents
                    if similar_crises:
                        st.markdown(f"**✅ Found {len(similar_crises)} similar past incidents:**")

                        for idx, result in enumerate(similar_crises, 1):
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    metadata = result.get("metadata", {})
                                    st.markdown(f"""
                                    **#{idx}. {metadata.get('type', 'Unknown').upper()} - {metadata.get('location', 'Unknown')}**
                                    
                                    📋 Description: {metadata.get('description', 'No description')}
                                    
                                    📍 Location: {metadata.get('location', 'Unknown')}
                                    
                                    ⚠️ Severity: {metadata.get('severity', 'Unknown').upper()}
                                    
                                    👥 Affected: {metadata.get('affected_people', 0):,} people
                                    
                                    ☠️ Casualties: {metadata.get('casualties', 0)}
                                    
                                    💰 Damage: {metadata.get('damage_estimate', 'Unknown')}
                                    
                                    ⏱️ Response Time: {metadata.get('response_time', 'Unknown')}
                                    """)

                                with col2:
                                    st.metric("Match Score", f"{result['similarity_score']}%")
                                    st.metric("Time Decay", f"{result.get('time_decay_factor', 1.0)}x")
                                    st.metric("Hours Old", f"{result.get('hours_old', 0):.1f}h")

                                st.divider()

                    else:
                        st.warning("⚠️ No similar incidents found in database")

                    # ============ SHOW RECOMMENDED PROTOCOL ============
                    st.markdown("### 📋 Recommended Protocol")

                    protocol = CRISIS_PROTOCOLS.get(crisis_type, {})
                    if protocol:
                        st.markdown(f"**Priority: {protocol['priority'].upper()}**")
                        st.markdown("**Actions to Take:**")
                        for i, action in enumerate(protocol["actions"], 1):
                            st.markdown(f"{i}. {action}")
                    else:
                        st.error("Unknown crisis type")

                    # ============ SAVE TO MEMORY ============
                    if st.button("💾 Save This Incident to Memory", use_container_width=True):
                        incident_id = qdrant_service.save_user_incident(
                            image_vector=hybrid_embedding.tolist(),
                            text_description=crisis_description,
                            metadata={
                                "type": crisis_type,
                                "location": "User Location",
                                "severity": severity,
                                "protocol": crisis_type,
                                "affected_people": 0
                            }
                        )
                        st.success(f"✅ Incident saved as #{incident_id} for future learning!")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

# ============ TAB 2: VIEW DATABASE ============
with tab2:
    st.markdown("### 📊 Qdrant Database Contents")

    if st.button("🔄 Refresh Database", use_container_width=True):
        all_crises = qdrant_service.get_all_crises()
        st.success(f"✅ Found {len(all_crises)} total incidents in database")

        # Group by type
        crisis_types = {}
        for crisis in all_crises:
            ctype = crisis.get("metadata", {}).get("type", "unknown")
            if ctype not in crisis_types:
                crisis_types[ctype] = []
            crisis_types[ctype].append(crisis)

        # Display by type
        for ctype, crises in crisis_types.items():
            with st.expander(f"**{ctype.upper()}** ({len(crises)} incidents)", expanded=False):
                for crisis in crises[:3]:  # Show first 3
                    metadata = crisis.get("metadata", {})
                    st.markdown(f"""
                    **{metadata.get('location')}**
                    - {metadata.get('description', 'No desc')[:100]}...
                    - Affected: {metadata.get('affected_people', 0):,}
                    - Time: {metadata.get('timestamp', 'Unknown')}
                    """)

# ============ TAB 3: PAST INCIDENTS ============
with tab3:
    st.markdown("### 📚 Historical Incidents in Database")

    crisis_types = {}
    all_crises = qdrant_service.get_all_crises()
    
    for crisis in all_crises:
        ctype = crisis.get("metadata", {}).get("type", "unknown")
        if ctype not in crisis_types:
            crisis_types[ctype] = len([c for c in all_crises if c.get("metadata", {}).get("type") == ctype])

    cols = st.columns(5)
    for i, (ctype, count) in enumerate(crisis_types.items()):
        with cols[i % 5]:
            st.metric(ctype.upper(), count)

    # Show detailed list
    selected_type = st.selectbox("Select crisis type to view", list(crisis_types.keys()))

    matching_crises = [c for c in all_crises if c.get("metadata", {}).get("type") == selected_type]

    for crisis in matching_crises[:10]:
        metadata = crisis.get("metadata", {})
        with st.container():
            st.markdown(f"""
            **{metadata.get('location')}** | {metadata.get('timestamp', 'Unknown')}
            
            {metadata.get('description', 'No description')}
            
            - Severity: {metadata.get('severity', 'Unknown')}
            - Affected: {metadata.get('affected_people', 0):,} people
            - Casualties: {metadata.get('casualties', 0)}
            """)
            st.divider()

# ============ TAB 4: INFO ============
with tab4:
    st.markdown("""
    ## 🚨 EchoGuard - System Information

    ### What is EchoGuard?
    EchoGuard is an AI-powered multimodal crisis response system that:
    - Analyzes disaster images + text descriptions
    - Finds similar past incidents from database
    - Recommends emergency response protocols
    - Learns from new incidents for future responses

    ### How It Works
    1. **Upload Crisis Image**: Provide visual evidence of the disaster
    2. **Describe Situation**: Add textual details about the crisis
    3. **AI Analysis**: CLIP model generates multimodal embeddings
    4. **Database Search**: Qdrant searches for similar historical incidents
    5. **Recommendations**: System suggests protocols based on similar cases
    6. **Learning**: New incidents saved for future reference

    ### Database
    - **Total Incidents**: 25 real case studies
    - **Crisis Types**: Flood, Fire, Earthquake, Landslide, Cyclone
    - **Data Source**: Real news reports from India (2024-2025)
    - **Vector DB**: Qdrant with CLIP embeddings

    ### Key Features
    - ✅ Multimodal Analysis (image + text)
    - ✅ Temporal Decay (recent incidents weighted higher)
    - ✅ Emergency Protocols (based on crisis type)
    - ✅ Continuous Learning (user incidents saved)
    - ✅ Similarity Matching (find relevant past cases)

    ### Technologies Used
    - **CLIP**: Vision-Language Model for embeddings
    - **Qdrant**: Vector database for similarity search
    - **Streamlit**: Web interface
    - **OpenAI API**: For reasoning (optional enhancement)

    ---
    **Version**: 2.0 FIXED | **Status**: ✅ Production Ready
    """)

st.divider()
st.markdown("<p style='text-align: center; color: #666;'>EchoGuard © 2025 - AI Crisis Response System</p>", unsafe_allow_html=True)
