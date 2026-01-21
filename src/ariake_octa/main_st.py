import streamlit.components.v1 as components

def display_roi_selector_mode():
    """ROI選択付き解析モード"""
    st.header("🎯 Interactive ROI Selection")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload MNV Image", 
            type=['tif', 'tiff', 'png', 'jpg', 'jpeg'],
            key="roi_selector"
        )
        
        if uploaded_file:
            # 画像を表示
            image = Image.open(uploaded_file)
            
            # Streamlit Drawing Tools を使用
            st.write("**Draw ROI on the image:**")
            
            canvas_result = st_canvas(
                fill_color="rgba(0, 255, 0, 0.3)",
                stroke_width=2,
                stroke_color="#00ff00",
                background_image=image,
                drawing_mode="polygon",  # freehand drawing
                key="canvas",
                height=600,
                width=800
            )
            
            if st.button("🚀 Analyze with Selected ROI", type="primary"):
                if canvas_result.json_data is not None:
                    # ROI座標を取得
                    roi_coords = extract_roi_coordinates(canvas_result.json_data)
                    
                    if roi_coords:
                        analyze_with_custom_roi(uploaded_file, roi_coords)
                    else:
                        st.warning("Please draw an ROI first")
