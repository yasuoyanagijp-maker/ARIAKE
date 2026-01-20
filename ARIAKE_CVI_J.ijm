// ARIAKE_CV_-J
// Choroidal vascularity index
// developed by Team Yanagi (2025)
// Originally developed for ARIAKE study
// version 1.2 (2025/12/1)

#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Results Output directory", style = "directory") t_original_output
#@ String (label = "file suffix", value = ".tif") suffix
#@ int (label = "Width = mm") scale_mm

// =====================================
// グローバルROI変数
// =====================================
var ROI_CHOROID = -1;
var ROI_RECT_1500 = -1;
var ROI_TOTAL_1500 = -1;
var ROI_RECT_3000 = -1;
var ROI_TOTAL_3000 = -1;
var ROI_LUMINAL = -1;
var ROI_LUMINAL_1500 = -1;
var ROI_LUMINAL_3000 = -1;
var ROI_DENOISED_LUMINAL = -1;
var ROI_DENOISED_3000 = -1;
var ROI_DENOISED_1500 = -1;

do {
    // Initialize counter
    var number_of_images = 0;
    var centroidx = 0;
    var centroidy = 0;
    var imagePath = 0;
    var endX = 0;
    var endY = 0;
    var errorLog = newArray();

    print("\\Clear");
    run("Close All");
    roiclose();
    
    var s_original_output = t_original_output;
    var mainFolder = File.getName(input);

    // 出力ディレクトリのサブフォルダ作成
    t_output = t_original_output + File.separator + mainFolder;
    if (!File.exists(t_output)) {
        File.makeDirectory(t_output);
    }
    s_output = s_original_output + File.separator + mainFolder + File.separator;
    if (!File.exists(s_output)) {
        File.makeDirectory(s_output);
    }

    // Start scanning
    countFilesInFolder(input, suffix);

    var size = number_of_images;
    var filteredList = newArray(size);
    var Luminal_Area = newArray(size);
    var Total_Choroidal_Area = newArray(size);
    var Denoised_Luminal_Area = newArray(size);
    var Choroidal_vascularity_index = newArray(size);
    var Denoised_Choroidal_vascularity_index = newArray(size);
    var Luminal_Area_3 = newArray(size);
    var Total_Choroidal_Area_3 = newArray(size);
    var Denoised_Luminal_Area_3 = newArray(size);
    var Choroidal_vascularity_index_3 = newArray(size);
    var Denoised_Choroidal_vascularity_index_3 = newArray(size);
    var Choroidal_Thickness = newArray(size);
    var Choroidal_Thickness_3 = newArray(size);
    var index = 0;

    processFolder(input);
    print("Total files found: " + filteredList.length);

    // Process each file
    for (i = 0; i < filteredList.length; i++) {
        processFile(input, filteredList[i], s_output);
    }

    // Save results
    Tabulate(s_output);

    // Get user signature
    Dialog.create("Put your signature");
    Dialog.addString("Analyst Name (Romaji):", "");
    Dialog.show();
    analystName = Dialog.getString();

    if (analystName == "") {
        showMessage("Warning", "分析者名が入力されていません。");
        analystName = "Unknown";
    }

    // Save parameters
    MonthNames = newArray("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec");
    DayNames = newArray("Sun", "Mon","Tue","Wed","Thu","Fri","Sat");
    getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
    TimeString ="Date, "+DayNames[dayOfWeek]+" ";
    if (dayOfMonth<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+dayOfMonth+"-"+MonthNames[month]+"-"+year+"\nTime, ";
    if (hour<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+hour+":";
    if (minute<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+minute+":";
    if (second<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+second;

    outputFilePath = t_output + File.separator + mainFolder+ "_Parameter.csv";
    if (!File.exists(outputFilePath)) {
        File.open(outputFilePath);
        File.append("Parameter,Value\n", outputFilePath);
    }

    File.append("" + TimeString + "\n", outputFilePath);
    File.append("Width (mm)," + scale_mm + "\n", outputFilePath);
    File.append("Analyzed by: " + analystName + "\n", outputFilePath);

    saveErrorLogWithSignature(s_output, analystName);

    run("Close All");
    roiclose();


	    // 次のフォルダに進むか確認
	    Dialog.create("確認");
	    Dialog.addMessage("他のフォルダーに進みますか?");
	    Dialog.addChoice("選択:はいの場合には次に患者フォルダを指定", newArray("はい", "いいえ、終了する"));
	    Dialog.show();
	    userChoice = Dialog.getChoice();
	
	    if (userChoice == "はい") {
	        run("Close All");
	        roiclose();
	        print("\\Clear");
	        input = getDirectory("Choose the main directory");
	        input = input + File.separator;
	    }
	    if (userChoice == "いいえ、終了する"){
	        run("Close All");
	        roiclose();
	        if (isOpen("Log")) {
	            selectWindow("Log");
	            run("Close");
	        }
	        exit;
    }
} while (userChoice == "はい");

run("Close All");
roiclose();
}


// =====================================
// FUNCTIONS
// =====================================

// Function to count files ->  return number_of_images
function countFilesInFolder(folder, suffix) {
    list = getFileList(folder);
    for (i = 0; i < list.length; i++) {
        if (endsWith(list[i], "/")) {
            countFilesInFolder(folder + File.separator + list[i], suffix);
        } else if (endsWith(list[i].toLowerCase(), suffix.toLowerCase())) {
            number_of_images++;
        }
    }
}

// Function to scan folders/subfolders/files to find files with the correct suffix
function processFolder(input) {
    list = getFileList(input);
    list = Array.sort(list);
    
    filteredList = newArray();

    for (i = 0; i < list.length; i++) {
        fullPath = input + File.separator + list[i];
        if (File.isDirectory(fullPath)) {
            processFolder(fullPath);
        } else if (endsWith(list[i], suffix)) {
            filteredList = Array.concat(filteredList, list[i]);
        }
    }
}

// Function to create results table
function Tabulate(output) { 
    if (filteredList.length == 0) {
        showMessage("Warning", "処理された画像がありません。");
        print("Warning: No images were processed");
        return;
    }
    
    table_name = "Results-CVI";
    Table.create(table_name);
    Table.setColumn("Image ID", filteredList);
    Table.setColumn("Total Choroidal Area (1500um)", Total_Choroidal_Area);
    Table.setColumn("Choroidal Thickness (1500um)", Choroidal_Thickness);   
    Table.setColumn("CVI (1500)", Choroidal_vascularity_index);
	Table.setColumn("Denoised CVI (1500)", Denoised_Choroidal_vascularity_index);
    Table.setColumn("Total Choroidal Area (3000um)", Total_Choroidal_Area_3);
   	Table.setColumn("Choroidal Thickness (3000um)", Choroidal_Thickness_3);    
    Table.setColumn("CVI (3000)", Choroidal_vascularity_index_3);
	Table.setColumn("Denoised CVI (3000)", Denoised_Choroidal_vascularity_index_3);
    Res_out = t_output + File.separator + mainFolder+ "_CVI.csv";
    saveAs(table_name, Res_out);
    print("Results saved to: " + Res_out);
    
    csvwindow = mainFolder+ "_CVI.csv";
    selectWindow(csvwindow);
    run("Close");
}

// Main processing function for each file
function processFile(input, file, output) {
    print("\n========================================");
    print("Processing: " + file);
    print("========================================");
    
    success = CVI(input, file, output);
    
    if (!success) {
        print("Failed to process: " + file);
        logError("Processing failed for: " + file);
        // 配列にNaN値を設定
        Total_Choroidal_Area[index] = NaN;
        Choroidal_vascularity_index[index] = NaN;
        Denoised_Choroidal_vascularity_index[index] = NaN;
        Total_Choroidal_Area_3[index] = NaN;
        Choroidal_vascularity_index_3[index] = NaN;
        Denoised_Choroidal_vascularity_index_3[index] = NaN;
        Choroidal_Thickness = NaN;
        Choroidal_Thickness_3 = NaN;
    }
    
    // 処理後に全ての画像を閉じる
    run("Close All");
    roiclose();
    
    index++;
    return success;
}

// Close ROI Manager if it is open
function roiclose(){
    if (isOpen("ROI Manager")) {
        selectWindow("ROI Manager");
        run("Close");
    }
}

// Main CVI calculation function
function CVI(input, file, output) {
    roiclose();
    
    // 初期セットアップ
    if (!performInitialImageSetup(input, file)) {
        print("Skipping file due to setup error: " + file);
        run("Close All");
        return false;
    }
    
    // 中心窩選択の検証
    if (!validateFoveaSelection()) {
        print("Skipping file due to fovea selection error: " + file);
        run("Close All");
        roiclose();
        return false;
    }

    // ノイズ除去
    denoised = denoise();
    
    // 画像処理と閾値設定
    if (!performImageThresholding(input, file)) {
        print("Skipping file due to thresholding error: " + file);
        run("Close All");
        roiclose();
        return false;
    }
    
    // 脈絡膜ROI選択の検証
    selectImage(denoised);
	
    run("Select None");
    
    if (!validateChoroidalROI()) {
        print("Skipping file due to choroidal ROI error: " + file);
        run("Close All");
        roiclose();
        return false;
    }
    
    // CVI測定の実行
    if (!performCVIMeasurements(input, file, output, denoised, imagePath)) {
        print("Skipping file due to measurement error: " + file);
        run("Close All");
        roiclose();
        return false;
    }
    
    print("Successfully processed: " + file);
    return true;
}

// Initial image setup function
function performInitialImageSetup(input, file) {
    print("Initial setup started: " + file);
    
    fullPath = input + File.separator + file;
    if (!File.exists(fullPath)) {
        print("Error: File does not exist - " + fullPath);
        return false;
    }
    
    open(fullPath);
    if (nImages == 0) {
        print("Error: Could not open image - " + file);
        return false;
    }
    
    run("Maximize");
    run("8-bit");
    
    imageWidth = getWidth();
    run("Set Scale...", "distance=" + imageWidth + " known=" + scale_mm + " unit=mm");
    run("Set Measurements...", "area standard center shape area_fraction redirect=None decimal=3");
    
    scale = scale_mm / imageWidth;
    xScale = scale;  
    aspectRatio = 2.29;
    yScale = xScale / aspectRatio;
    run("Properties...", "pixel_width=" + xScale + " pixel_height=" + yScale + " global");
    
    print("Initial setup completed for: " + file);
    return true;
}

// Validate fovea selection
function validateFoveaSelection() {
    roiManager("Reset");
    setTool("point");
    waitForUser("Select the fovea using the point tool in ROI Manager and press OK.");
    
    // 選択が行われたか確認
    if (selectionType() == -1) {
        showMessage("Error", "中心窩が選択されていません。\nこの画像をスキップします。");
        print("Error: No fovea selection made");
        return false;
    }
    
    roiManager("add");
    
    if (roiManager("count") == 0) {
        showMessage("Error", "ROIの追加に失敗しました。\nこの画像をスキップします。");
        print("Error: Failed to add fovea ROI");
        return false;
    }
    
    roiManager("Select", roiManager("count")-1);
    
    // 中心座標の取得
    run("Set Measurements...", "area standard center shape area_fraction redirect=None decimal=3");
    roiManager("measure");
    
    if (nResults == 0) {
        showMessage("Error", "中心窩の測定に失敗しました。");
        print("Error: Failed to measure fovea");
        return false;
    }
    
    scale = scale_mm / getWidth();
    centroidx = getResult("X", nResults-1) / scale;
    centroidy = getResult("Y", nResults-1) / scale;
    
    print("Fovea selected at: X=" + centroidx + ", Y=" + centroidy);
    
    // Create a new rectangular ROI centered on the fovea point
    Path = getImageID();
    new_width = 3.2 / scale;
    new_height = getHeight();
    
    // グローバル変数に代入(varを付けない)
    startX = centroidx - new_width / 2;
    startY = 0;
    endX = centroidx + new_width / 2;
    endY = new_height;
    
    makeRectangle(startX, startY, new_width, new_height);
    roiManager("Add");
    
    print("ROI bounds - startX: " + startX + ", endX: " + endX + ", startY: " + startY + ", endY: " + endY);
    
    return true;
}

// Validate choroidal ROI selection
function validateChoroidalROI() {
    setTool(2); //
    waitForUser("強調表示された部分の脈絡膜領域を取り囲んでください");
    
    // 選択が行われたか確認
    if (selectionType() == -1) {
        showMessage("Error", "脈絡膜領域が選択されていません。\nこの画像をスキップします。");
        print("Error: No choroidal region selected");
        return false;
    }
    
    // ROIを保存
    roiManager("Add");
    
    if (roiManager("count") == 0) {
        showMessage("Error", "脈絡膜ROIの追加に失敗しました。");
        print("Error: Failed to add choroidal ROI");
        return false;
    }
    
    print("Choroidal ROI added successfully");
    return true;
}
function performImageThresholding(input, file) {
    open(input + File.separator + file);
    if (nImages == 0) {
        print("Error: Could not reopen image for thresholding");
        return false;
    }
    
    imagePath = getImageID();  // ← グローバル変数に代入
    run("8-bit");
    imageWidth = getWidth();
    run("Set Scale...", "distance=" + imageWidth + " known=" + scale_mm + " unit=mm");
    
    scale = scale_mm / imageWidth;
    
    run("Duplicate...", "title=temp ignore");
    setThreshold(50, 255);
    setOption("BlackBackground", true);
    run("Auto Local Threshold", "method=Niblack parameter=2 black");
    
    selectImage("temp");
    roiManager("show all");
    roiManager("select", roiManager("count")-1);
    run("Analyze Particles...", "size=0.0001-Infinity add");
    
    if (roiManager("count") < 2) {
        print("Error: Insufficient ROIs after particle analysis");
        return false;
    }
    
    roiManager("Combine");
    roiManager("Add");
    roiManager("select", roiManager("count")-1);
    selectImage(imagePath);
    run("Measure");
    
    if (nResults == 0) {
        print("Error: Failed to measure luminal luminance");
        return false;
    }
    
    luminalLuminance = getResult("Mean", nResults-1);
    close("Results");
    
    selectImage(imagePath);
    setMinAndMax(luminalLuminance, 255);
    run("Apply LUT");
    run("Auto Local Threshold", "method=Niblack radius=15 parameter_1=0 parameter_2=0 white");
    roiclose();
    
    return true;  // ← 元のまま
}
// Wait for ROI with timeout
function waitForROIWithTimeout(requiredCount, timeoutSeconds) {
    timeout = 0;
    maxTimeout = timeoutSeconds * 2; // 0.5秒間隔なので2倍
    
    while (roiManager("Count") < requiredCount && timeout < maxTimeout) {
        wait(500);
        timeout++;
    }
    
    if (timeout >= maxTimeout) {
        print("Error: ROI processing timeout (required: " + requiredCount + ", current: " + roiManager("Count") + ")");
        return false;
    }
    
    return true;
}



// Error logging function
function logError(message) {
    MonthNames = newArray("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec");
    DayNames = newArray("Sun", "Mon","Tue","Wed","Thu","Fri","Sat");
    getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
    
    TimeString = DayNames[dayOfWeek] + " ";
    if (dayOfMonth<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+dayOfMonth+"-"+MonthNames[month]+"-"+year+" ";
    if (hour<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+hour+":";
    if (minute<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+minute+":";
    if (second<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+second;
    
    timestamp = "[" + TimeString + "] ";
    errorLog = Array.concat(errorLog, timestamp + message);
    print("ERROR: " + message);
}

// Save error log with signature
function saveErrorLogWithSignature(output, analystName) {
    // 日付と時刻取得
    MonthNames = newArray("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec");
    DayNames = newArray("Sun", "Mon","Tue","Wed","Thu","Fri","Sat");
    getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);

    TimeString = DayNames[dayOfWeek] + " ";
    if (dayOfMonth<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+dayOfMonth+"-"+MonthNames[month]+"-"+year+" ";
    if (hour<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+hour+":";
    if (minute<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+minute+":";
    if (second<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+second;

    logPath = output + File.separator + mainFolder + "_error_log.txt";
    logHeader = "==============================================\n";
    logHeader = logHeader + "Error Log for: " + mainFolder + "\n";
    logHeader = logHeader + "Generated: " + TimeString + "\n";
    logHeader = logHeader + "Analyzed by: " + analystName + "\n";
    logHeader = logHeader + "==============================================\n\n";

    // エラーがある場合はログ内容を追加、ない場合は「No errors」と書く
    if (errorLog.length > 0) {
        logContent = logHeader + String.join(errorLog, "\n");
    } else {
        logContent = logHeader + "No errors encountered during processing.\n";
    }

    logContent = logContent + "\n\n==============================================\n";
    logContent = logContent + "End of Error Log\n";
    logContent = logContent + "==============================================";

    File.saveString(logContent, logPath);
    print("\nError log saved to: " + logPath);
}

// =====================================
// 改善された performCVIMeasurements 関数
// =====================================

function performCVIMeasurements(input, file, output, denoised, imagePath) {
    print("Starting CVI measurements for: " + file);
    
    // ROIインデックスをリセット
    resetROIIndices();
    
    // 変数の検証
    if (isNaN(centroidx) || centroidx == 0) {
        print("Error: Invalid centroidx value: " + centroidx);
        return false;
    }
    
    if (isNaN(scale_mm) || scale_mm == 0) {
        print("Error: Invalid scale_mm value: " + scale_mm);
        return false;
    }
    
    // 画像の選択と検証
    selectImage(denoised);
    
    // 画像が正しく選択されたか確認
    if (getImageID() != denoised) {
        print("Warning: Image selection may have failed, retrying...");
        wait(100);
        selectImage(denoised);
    }
    
    // 画像のサイズを取得
    imageWidth = getWidth();
    imageHeight = getHeight();
    scale = scale_mm / imageWidth;
    
    // ROI 0: 脈絡膜の輪郭(すでに追加されているはず)
    if (roiManager("count") == 0) {
        print("Error: No choroidal ROI found");
        return false;
    }
    ROI_CHOROID = 0;
    print("Choroidal ROI at index: " + ROI_CHOROID);
    
    // === 1500μm ROI ===
    width_1500 = 1.5 / scale;
    height_roi = imageHeight;
    x_1500 = centroidx - width_1500 / 2;
    y_roi = 0;
    
    // 境界チェック
    if (x_1500 < 0) {
        print("Warning: 1500um ROI extends beyond left boundary");
        x_1500 = 0;
    }
    if (x_1500 + width_1500 > imageWidth) {
        print("Warning: 1500um ROI extends beyond right boundary");
        width_1500 = imageWidth - x_1500;
    }
    
    makeRectangle(x_1500, y_roi, width_1500, height_roi);
    roiManager("Add");
    ROI_RECT_1500 = roiManager("count") - 1;
    print("Added 1500um rectangle ROI at index: " + ROI_RECT_1500);
    
    // AND演算: 脈絡膜領域 AND 1500um ROI
    roiManager("Select", newArray(ROI_CHOROID, ROI_RECT_1500));
    roiManager("and");
    roiManager("Add");
    ROI_TOTAL_1500 = roiManager("count") - 1;
    print("Added Total Area (1500um) ROI at index: " + ROI_TOTAL_1500);
    
    // Total Choroidal Areaの測定
    selectImage(imagePath);
    roiManager("Select", ROI_TOTAL_1500);
    run("Measure");
    
    if (nResults == 0) {
        print("Error: Failed to measure Total Choroidal Area (1500um)");
        return false;
    }
    
    Total_Choroidal_Area[index] = getResult("Area", nResults - 1);
    print("Total Choroidal Area (1500um): " + Total_Choroidal_Area[index]);
    Choroidal_Thickness[index] = Total_Choroidal_Area[index] * 1000 / 1.5;
    print("Choroidal Thickness (um): " + Choroidal_Thickness[index]);
        
    // === 3000μm ROI ===
    width_3000 = 3.0 / scale;
    x_3000 = centroidx - width_3000 / 2;
    
    // 境界チェック
    if (x_3000 < 0) {
        print("Warning: 3000um ROI extends beyond left boundary");
        x_3000 = 0;
    }
    if (x_3000 + width_3000 > imageWidth) {
        print("Warning: 3000um ROI extends beyond right boundary");
        width_3000 = imageWidth - x_3000;
    }
    
    makeRectangle(x_3000, y_roi, width_3000, height_roi);
    roiManager("Add");
    ROI_RECT_3000 = roiManager("count") - 1;
    print("Added 3000um rectangle ROI at index: " + ROI_RECT_3000);
    
    // AND演算: 脈絡膜領域 AND 3000um ROI
    roiManager("Select", newArray(ROI_CHOROID, ROI_RECT_3000));
    roiManager("and");
    roiManager("Add");
    ROI_TOTAL_3000 = roiManager("count") - 1;
    print("Added Total Area (3000um) ROI at index: " + ROI_TOTAL_3000);
    
    // Total Choroidal Area (3000um)の測定
    roiManager("Select", ROI_TOTAL_3000);
    run("Measure");
    
    if (nResults == 0) {
        print("Error: Failed to measure Total Choroidal Area (3000um)");
        return false;
    }
    
    Total_Choroidal_Area_3[index] = getResult("Area", nResults - 1);
    print("Total Choroidal Area (3000um): " + Total_Choroidal_Area_3[index]);
    Choroidal_Thickness_3[index] = Total_Choroidal_Area_3[index] * 1000 / 3;
    print("Macular Choroidal Thickness (um): " + Choroidal_Thickness_3[index]);
    
    // === Luminal Area (血管腔)の測定 ===
    selectImage(imagePath);
    run("Despeckle");
    run("Invert");
    run("Create Selection");
    
    if (selectionType() == -1) {
        print("Warning: No luminal selection created");
        Luminal_Area[index] = 0;
        Luminal_Area_3[index] = 0;
    } else {
        roiManager("add");
        ROI_LUMINAL = roiManager("count") - 1;
        print("Added Luminal ROI at index: " + ROI_LUMINAL);
        
        // Luminal Area (1500um)
        roiManager("Select", newArray(ROI_TOTAL_1500, ROI_LUMINAL));
        roiManager("and");
        
        if (selectionType() == -1) {
            print("Warning: No intersection for Luminal Area (1500um)");
            Luminal_Area[index] = 0;
        } else {
            roiManager("Add");
            ROI_LUMINAL_1500 = roiManager("count") - 1;
            roiManager("Select", ROI_LUMINAL_1500);
            run("Measure");
            
            if (nResults > 0) {
                Luminal_Area[index] = getResult("Area", nResults - 1);
                print("Luminal Area (1500um): " + Luminal_Area[index]);
            } else {
                Luminal_Area[index] = 0;
            }
        }
        
        // Luminal Area (3000um)
        roiManager("Select", newArray(ROI_TOTAL_3000, ROI_LUMINAL));
        roiManager("and");
        
        if (selectionType() == -1) {
            print("Warning: No intersection for Luminal Area (3000um)");
            Luminal_Area_3[index] = 0;
        } else {
            roiManager("Add");
            ROI_LUMINAL_3000 = roiManager("count") - 1;
            roiManager("Select", ROI_LUMINAL_3000);
            run("Measure");
            
            if (nResults > 0) {
                Luminal_Area_3[index] = getResult("Area", nResults - 1);
                print("Luminal Area (3000um): " + Luminal_Area_3[index]);
            } else {
                Luminal_Area_3[index] = 0;
            }
        }
    }
    
    // === CVI計算 ===
    if (Total_Choroidal_Area[index] > 0) {
        Choroidal_vascularity_index[index] = (Luminal_Area[index] / Total_Choroidal_Area[index]) * 100;
        print("CVI (1500um): " + Choroidal_vascularity_index[index] + "%");
    } else {
        Choroidal_vascularity_index[index] = NaN;
        print("Warning: Total Choroidal Area (1500um) is zero - CVI cannot be calculated");
    }
    
    if (Total_Choroidal_Area_3[index] > 0) {
        Choroidal_vascularity_index_3[index] = (Luminal_Area_3[index] / Total_Choroidal_Area_3[index]) * 100;
        print("CVI (3000um): " + Choroidal_vascularity_index_3[index] + "%");
    } else {
        Choroidal_vascularity_index_3[index] = NaN;
        print("Warning: Total Choroidal Area (3000um) is zero - CVI cannot be calculated");
    }
    
    // === 画像保存 ===
    open(input + File.separator + file);
    if (nImages > 0 && ROI_LUMINAL_3000 >= 0) {
        roiManager("select", ROI_LUMINAL_3000);
        setColor(0, 0, 0);  // 黒色を設定（RGBで0,0,0）
		run("Fill");  
        saveStage(output, file, Choroidal_vascularity_index[index], "CVI_");
    }
    
    close("Results");
    if (isOpen("temp")) {
        close("temp");
    }
    
    // === Denoised測定 ===
    if (!performDenoisedMeasurements(input, file, output, denoised, imagePath)) {
        print("Warning: Denoised measurements failed");
        Denoised_Choroidal_vascularity_index[index] = NaN;
        Denoised_Choroidal_vascularity_index_3[index] = NaN;
    }
    
    print("CVI measurements completed for: " + file);
    print("Final ROI count: " + roiManager("count"));
    
    return true;
}

// =====================================
// 改善された denoise 関数
// =====================================
// Fixed denoise() function for ImageJ Macro
function denoise() {
    print("Starting denoise process");

    originalImageID = getImageID();
    originalTitle = getTitle();

    selectImage(originalImageID);
    width = getWidth();
    height = getHeight();

    if (isNaN(centroidx) || isNaN(scale_mm)) {
        print("Error: Invalid parameters for denoise");
        return originalImageID;
    }

    scale = scale_mm / width;
    roi_width = 3.2 / scale;

    roi_startX = round(centroidx - roi_width / 2);
    roi_startX = maxOf(0, roi_startX);
    roi_endX = roi_startX + round(roi_width);
    if (roi_endX > width) roi_endX = width;

    roi_startY = 0;
    roi_endY = height;

    roi_width_int = roi_endX - roi_startX;
    roi_height_int = roi_endY - roi_startY;

    print("ROI width int: " + roi_width_int);
    print("ROI height int: " + roi_height_int);

    roiPixelCount = roi_width_int * roi_height_int;

    JrawArray = newArray(roiPixelCount);
    SumJrawArray = newArray(roiPixelCount);
    EnhancedArray = newArray(roiPixelCount);

    point = 0;
    for (y = roi_startY; y < roi_endY; y++) {
        for (x = roi_startX; x < roi_endX; x++) {
            pixelValue = getPixel(x, y);
            JrawArray[point] = pow(pixelValue / 255.0, 4);
            point++;
        }
    }

    print("Filled JrawArray: " + point + " pixels");

    for (col = 0; col < roi_width_int; col++) {
        bottom_index = col + (roi_height_int - 1) * roi_width_int;
        SumJrawArray[bottom_index] = pow(JrawArray[bottom_index], 2);

        for (row = roi_height_int - 2; row >= 0; row--) {
            current_index = col + row * roi_width_int;
            below_index = col + (row + 1) * roi_width_int;
            SumJrawArray[current_index] = pow(JrawArray[current_index], 2) + SumJrawArray[below_index];
        }
    }

    totalPixels = roiPixelCount;
    for (point = 0; point < totalPixels; point++) {
        Jraw_n = pow(JrawArray[point], 2);
        sumJraw = SumJrawArray[point];
        if (sumJraw > 0) {
            enhancedValue = 255 * pow(Jraw_n / (2 * sumJraw), 0.25);
            EnhancedArray[point] = round(enhancedValue);
        } else {
            EnhancedArray[point] = 0;
        }
    }

    point = 0;
    for (y = roi_startY; y < roi_endY; y++) {
        for (x = roi_startX; x < roi_endX; x++) {
            setPixel(x, y, EnhancedArray[point]);
            point++;
        }
    }

    run("Despeckle");
    print("Denoise finished successfully.");
    return originalImageID;
}

// =====================================
// performDenoisedMeasurements 関数
// =====================================

function performDenoisedMeasurements(input, file, output, denoised, imagePath) {
    print("Starting denoised measurements for: " + file);
    
    // 必要なROIが存在するか確認
    if (ROI_TOTAL_1500 < 0 || ROI_TOTAL_3000 < 0) {
        print("Error: Required ROIs not found (1500um: " + ROI_TOTAL_1500 + ", 3000um: " + ROI_TOTAL_3000 + ")");
        return false;
    }
    
    // Denoised画像の二値化処理
    selectImage(denoised);
	roiManager("Deselect");
	run("Select None");
    roiManager("Show None");
    run("Duplicate...", "title=temp ignore");
 
    if (!isOpen("temp")) {
        print("Error: Failed to create temp image");
        return false;
    }
    
    selectImage("temp");
    

    // ✅ 画像タイプを確認して8-bitに変換
    imagedepth = bitDepth();
    if (imagedepth != 8) {
        print("Converting from " + imagedepth + "-bit to 8-bit for threshold processing");
        run("8-bit");
    }
    
    run("Auto Local Threshold", "method=Niblack parameter=2 black");

	run("Options...", "iterations=1 count=1 black do=Open");
	run("Options...", "iterations=1 count=1 black do=Close");
    
    // 反復的なDespeckle(変化がなくなるまで)
    print("Applying iterative despeckle...");
    run("Despeckle");
    

    wait(500);
    
    iterationCount = 0;
    maxIterations = 20;
    
    do {
        getStatistics(area1);
        run("Despeckle");
        wait(500);
        getStatistics(area2);
        iterationCount++;
        
        if (iterationCount >= maxIterations) {
            print("Warning: Max despeckle iterations reached (" + maxIterations + ")");
            break;
        }
    } while (area1 != area2);
    
    print("Despeckle completed after " + iterationCount + " iterations");
    
    // 穴埋めと選択範囲作成
    run("Fill Holes");
    run("Select All");
    run("Create Selection");
    
    if (selectionType() == -1) {
        print("Warning: No selection created from denoised image");
        close("temp");
        return false;
    }
    
	roiManager("add");
    ROI_DENOISED_LUMINAL = roiManager("count") - 1;
    print("Added denoised luminal ROI at index: " + ROI_DENOISED_LUMINAL);
    

    // === 3000um Denoised Luminal Area ===
    roiManager("Select", newArray(ROI_TOTAL_3000, ROI_DENOISED_LUMINAL));
    roiManager("and");

    if (selectionType() == -1) {
        print("Warning: No intersection for denoised luminal area (3000um)");
        Denoised_Luminal_Area_3[index] = 0;
    } else {
        roiManager("Add");
        ROI_DENOISED_3000 = roiManager("count") - 1;
        print("Added denoised luminal 3000um ROI at index: " + ROI_DENOISED_3000);
        
        roiManager("Select", ROI_DENOISED_3000);
        run("Measure");
        
        if (nResults > 0) {
            Denoised_Luminal_Area_3[index] = getResult("Area", nResults - 1);
            print("Denoised Luminal Area (3000um): " + Denoised_Luminal_Area_3[index]);
        } else {
            Denoised_Luminal_Area_3[index] = 0;
            print("Warning: Failed to measure denoised luminal area (3000um)");
        }
    }
    
    // CVI計算(3000um)
    if (Total_Choroidal_Area_3[index] > 0) {
        Denoised_Choroidal_vascularity_index_3[index] = (Denoised_Luminal_Area_3[index] / Total_Choroidal_Area_3[index]) * 100;
        print("Denoised CVI (3000um): " + Denoised_Choroidal_vascularity_index_3[index] + "%");
    } else {
        Denoised_Choroidal_vascularity_index_3[index] = NaN;
        print("Warning: Cannot calculate Denoised CVI (3000um) - Total Area is zero");
    }
    
    // === 1500um Denoised Luminal Area ===
    roiManager("show none");
    roiManager("Select", newArray(ROI_TOTAL_1500, ROI_DENOISED_LUMINAL));
    roiManager("and");
    
    if (selectionType() == -1) {
        print("Warning: No intersection for denoised luminal area (1500um)");
        Denoised_Luminal_Area[index] = 0;
    } else {
        roiManager("Add");
        ROI_DENOISED_1500 = roiManager("count") - 1;
        print("Added denoised luminal 1500um ROI at index: " + ROI_DENOISED_1500);
        
        roiManager("Select", ROI_DENOISED_1500);
        run("Measure");
        
        if (nResults > 0) {
            Denoised_Luminal_Area[index] = getResult("Area", nResults - 1);
            print("Denoised Luminal Area (1500um): " + Denoised_Luminal_Area[index]);
        } else {
            Denoised_Luminal_Area[index] = 0;
            print("Warning: Failed to measure denoised luminal area (1500um)");
        }
    }
    
    // CVI計算(1500um)
    if (Total_Choroidal_Area[index] > 0) {
        Denoised_Choroidal_vascularity_index[index] = (Denoised_Luminal_Area[index] / Total_Choroidal_Area[index]) * 100;
        print("Denoised CVI (1500um): " + Denoised_Choroidal_vascularity_index[index] + "%");
    } else {
        Denoised_Choroidal_vascularity_index[index] = NaN;
        print("Warning: Cannot calculate Denoised CVI (1500um) - Total Area is zero");
    }
    
    // === 画像の保存 ===
    open(input + File.separator + file);
    
    if (nImages > 0 && ROI_DENOISED_3000 >= 0) {
        roiManager("show none");
        roiManager("select", ROI_DENOISED_3000);
        setColor(0, 0, 0);  // 黒色を設定（RGBで0,0,0）
		run("Fill");  
        saveStage(output, file, Denoised_Choroidal_vascularity_index[index], "Denoise_CVI_");
    }
    
    // クリーンアップ
    close("Results");
    
    if (isOpen("temp")) {
        close("temp");
    }
    
    print("Denoised measurements completed");
    print("Final ROI count: " + roiManager("count"));
    
    return true;
}
// ROIインデックスをリセット
function resetROIIndices() {
    ROI_CHOROID = -1;
    ROI_RECT_1500 = -1;
    ROI_TOTAL_1500 = -1;
    ROI_RECT_3000 = -1;
    ROI_TOTAL_3000 = -1;
    ROI_LUMINAL = -1;
    ROI_LUMINAL_1500 = -1;
    ROI_LUMINAL_3000 = -1;
    ROI_DENOISED_LUMINAL = -1;
    ROI_DENOISED_3000 = -1;
    ROI_DENOISED_1500 = -1;
}
// Function to Save Intermediate Stages
function saveStage(s_output, file, text, name_string){
	run("Duplicate...", "title=duplicate.jpg ignore");
	selectWindow("duplicate.jpg");
    
    // 画像サイズを取得
    var width = getWidth();
    var height = getHeight();

    var fontSize = height * 0.05;
    setFont("SanSerif", fontSize, "Plain");

    // 文字の位置を指定（中央下）
    var textWidth = getStringWidth(text);
    var x = (width - textWidth) / 2;
    var y = height - (fontSize * 2.1);

    // テキスト本体を描画
    setFont("SanSerif", fontSize, "Plain");
    setForegroundColor(255, 255, 255);
    makeText(text, x, y);
    run("Add Selection...");
    run("Fill", "slice");
    run("Set Scale...", "distance=" + getWidth() + " known=" + scale_mm + " unit=mm");
	run("Scale Bar...", "width=1.0 height=0.2 color=Yellow horizontal bold overlay");
	
	// 保存
	saveAs("jpg", s_output + File.separator + name_string + file);
	run("Close");
}


// =====================================
// END OF MACRO
// =====================================