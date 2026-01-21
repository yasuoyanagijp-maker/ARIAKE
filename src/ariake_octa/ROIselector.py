def display_single_image_mode_with_roi(scale_mm: float, save_stages: bool):
    """ROI選択機能付きの単一画像解析"""
    st.header("🎯 Single Image Analysis with ROI Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload MNV Image",
            type=['tif', 'tiff', 'png', 'jpg', 'jpeg'],
            help="Select the MNV image to analyze",
            key="roi_image"
        )
    
    with col2:
        roi_mode = st.radio(
            "ROI Selection Mode",
            ["🤖 Automatic Detection", "✏️ Manual Selection"],
            help="Choose how to define the region of interest"
        )
    
    if uploaded_file is not None:
        # 画像を読み込み
        image_bytes = uploaded_file.read()
        
        if roi_mode == "✏️ Manual Selection":
            st.subheader("Draw ROI on the Image")
            st.info("💡 Click and drag to draw a freehand region around the MNV lesion. The selection will be closed automatically.")
            
            # PIL Image として読み込み
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Canvas で描画
            canvas_result = st_canvas(
                fill_color="rgba(0, 255, 0, 0.3)",
                stroke_width=2,
                stroke_color="#00FF00",
                background_image=pil_image,
                update_streamlit=True,
                drawing_mode="freedraw",
                point_display_radius=0,
                key="canvas",
                height=min(pil_image.height, 600),
                width=min(pil_image.width, 800),
            )
            
            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                if st.button("🚀 Analyze with Manual ROI", type="primary", use_container_width=True):
                    if canvas_result.image_data is not None:
                        # Canvas から ROI マスクを抽出
                        roi_mask = extract_roi_from_canvas(canvas_result.image_data, pil_image.size)
                        
                        if roi_mask is not None and roi_mask.sum() > 0:
                            analyze_with_custom_roi(image_bytes, roi_mask, scale_mm, save_stages)
                        else:
                            st.error("❌ Please draw an ROI on the image first")
                    else:
                        st.error("❌ Please draw an ROI on the image first")
            
            with col_b:
                if st.button("🔄 Clear ROI", use_container_width=True):
                    st.rerun()
        
        else:  # Automatic Detection
            st.info("💡 ROI will be automatically detected from the image")
            
            if st.button("🚀 Analyze with Auto-Detection", type="primary"):
                # 元のファイルを再度開く
                uploaded_file.seek(0)
                analyze_single_image(uploaded_file, None, scale_mm, save_stages)


def extract_roi_from_canvas(canvas_data, original_size):
    """Canvas データから ROI マスクを抽出"""
    import numpy as np
    import cv2
    
    # Canvas データ（RGBA）から緑チャンネルを取得（描画部分）
    if canvas_data is None:
        return None
    
    # 緑色の描画部分を抽出
    green_channel = canvas_data[:, :, 1]
    
    # 閾値処理で ROI を抽出
    roi_mask = (green_channel > 0).astype(np.uint8) * 255
    
    # 元の画像サイズにリサイズ
    if roi_mask.shape[:2] != original_size[::-1]:
        roi_mask = cv2.resize(roi_mask, original_size, interpolation=cv2.INTER_NEAREST)
    
    return roi_mask


def analyze_with_custom_roi(image_bytes, roi_mask, scale_mm, save_stages):
    """カスタムROIを使用して解析"""
    st.session_state.log_messages = []
    add_log("Starting analysis with custom ROI...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 画像を保存
            image_path = temp_path / "input_image.tif"
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            add_log(f"Saved image: {image_path.name}")
            progress_bar.progress(20)
            
            # ROI マスクを保存
            roi_path = temp_path / "roi_mask.png"
            import cv2
            cv2.imwrite(str(roi_path), roi_mask)
            add_log("ROI mask created")
            
            progress_bar.progress(30)
            status_text.text("Analyzing with custom ROI...")
            
            # MNV Pipeline で解析
            from src.core.mnv_pipeline import MNVPipeline
            
            pipeline = MNVPipeline(
                scale_mm=scale_mm,
                save_stages=save_stages
            )
            
            output_dir = temp_path / "output"
            output_dir.mkdir(exist_ok=True)
            
            # 画像とROIマスクを読み込み
            import cv2
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            
            # ROI を適用して解析
            results = pipeline.analyze(
                image_path=str(image_path),
                output_dir=str(output_dir),
                custom_roi_mask=roi_mask  # カスタムROIを渡す
            )
            
            progress_bar.progress(90)
            add_log("Analysis completed successfully!")
            
            # 結果を表示
            display_single_image_results(results, output_dir)
            
            progress_bar.progress(100)
            status_text.empty()
            
            st.success("✅ Analysis completed successfully with custom ROI!")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        add_log(f"Error: {str(e)}")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
