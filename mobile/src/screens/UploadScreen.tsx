import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import { uploadVideo, uploadScreenshot, startAnalysis } from "../services/api";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937", red: "#EF4444" };

export default function UploadScreen({ navigation }: any) {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [selectedWorkout, setSelectedWorkout] = useState<string | null>(null);
  const [screenshotStats, setScreenshotStats] = useState<any>(null);
  const [status, setStatus] = useState("");

  const pickVideo = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: "video/*", copyToCacheDirectory: true });
    if (result.canceled || !result.assets?.length) return;
    const asset = result.assets[0];
    setStatus("Uploading…");
    try { const d = await uploadVideo(asset.uri, asset.name); setVideoId(d.video_id); setStatus(""); Alert.alert("Ready", "Video uploaded successfully"); }
    catch (e: any) { Alert.alert("Error", e.message); setStatus(""); }
  };

  const pickScreenshot = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) { Alert.alert("Permission needed"); return; }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: "images", quality: 0.9 });
    if (result.canceled || !result.assets?.length) return;
    setStatus("Extracting stats…");
    try {
      const data = await uploadScreenshot(result.assets[0].uri);
      if (data.workout_id) { setSelectedWorkout(data.workout_id); setScreenshotStats(data.extracted_stats); setStatus(""); }
      else { setStatus(""); Alert.alert("Notice", "Could not read stats. You can still proceed."); }
    } catch { setStatus(""); }
  };

  const handleStart = async () => {
    if (!videoId) { Alert.alert("Upload a video first"); return; }
    try { const r = await startAnalysis(videoId, selectedWorkout || undefined); navigation.navigate("AnalysisProgress", { taskId: r.task_id }); }
    catch (e: any) { Alert.alert("Failed", e.message); }
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>New Analysis</Text>

      <TouchableOpacity style={styles.step} onPress={pickVideo} activeOpacity={0.7}>
        <View style={styles.stepIcon}><Text style={styles.stepNum}>1</Text></View>
        <View style={styles.stepContent}>
          <Text style={styles.stepTitle}>{videoId ? "Video Ready" : "Select Video"}</Text>
          <Text style={styles.stepSub}>{videoId ? "✅ Compressed & uploaded" : "Tap to choose from library"}</Text>
        </View>
        <Text style={styles.stepArrow}>→</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.step} onPress={pickScreenshot} activeOpacity={0.7}>
        <View style={[styles.stepIcon, screenshotStats && { backgroundColor: C.accent }]}>
          <Text style={[styles.stepNum, screenshotStats && { color: "#0A0D14" }]}>{screenshotStats ? "✓" : "2"}</Text>
        </View>
        <View style={styles.stepContent}>
          <Text style={styles.stepTitle}>OPPO Watch Screenshot</Text>
          <Text style={styles.stepSub}>{screenshotStats ? `📊 ${screenshotStats.total_shots} shots · ${screenshotStats.avg_heart_rate} bpm` : "Optional — tap to add watch data"}</Text>
        </View>
        <Text style={styles.stepArrow}>→</Text>
      </TouchableOpacity>

      {status ? <Text style={styles.status}>{status}</Text> : null}

      <TouchableOpacity style={[styles.startBtn, !videoId && { opacity: 0.4 }]} onPress={handleStart} disabled={!videoId} activeOpacity={0.8}>
        <Text style={styles.startBtnText}>Start AI Analysis</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  title: { fontSize: 28, fontWeight: "800", color: C.text, marginTop: 50, marginBottom: 28 },
  step: { backgroundColor: C.card, borderRadius: 16, padding: 18, marginBottom: 12, flexDirection: "row", alignItems: "center", borderWidth: 1, borderColor: C.border },
  stepIcon: { width: 36, height: 36, borderRadius: 18, backgroundColor: "#1F2937", alignItems: "center", justifyContent: "center", marginRight: 14 },
  stepNum: { fontSize: 16, fontWeight: "700", color: C.sub },
  stepContent: { flex: 1 },
  stepTitle: { fontSize: 16, fontWeight: "600", color: C.text },
  stepSub: { fontSize: 12, color: C.muted, marginTop: 3 },
  stepArrow: { fontSize: 20, color: C.muted },
  status: { textAlign: "center", color: C.accent, fontSize: 13, marginVertical: 8 },
  startBtn: { backgroundColor: C.accent, borderRadius: 16, padding: 18, alignItems: "center", marginTop: 20 },
  startBtnText: { color: "#0A0D14", fontSize: 17, fontWeight: "700" },
});
