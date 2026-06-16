import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import { uploadVideo, uploadScreenshot, startAnalysis } from "../services/api";

export default function UploadScreen({ navigation }: any) {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [selectedWorkout, setSelectedWorkout] = useState<string | null>(null);
  const [screenshotStats, setScreenshotStats] = useState<any>(null);
  const [status, setStatus] = useState("");

  const pickVideo = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: "video/*", copyToCacheDirectory: true });
    if (result.canceled || !result.assets?.length) return;
    const asset = result.assets[0];

    setStatus("Compressing...");
    const outPath = `${FileSystem.cacheDirectory}comp_${Date.now()}.mp4`;
    try {
      const { FFmpegKit } = require("ffmpeg-kit-react-native");
      await FFmpegKit.execute(`-i ${asset.uri} -vf "scale=-2:720,fps=30" -c:v libx264 -b:v 4M -c:a aac -b:a 128k -y ${outPath}`);
    } catch {}

    setStatus("Uploading...");
    try {
      const data = await uploadVideo(outPath, "video.mp4");
      setVideoId(data.video_id);
      setStatus("Ready");
      Alert.alert("Success", "Video uploaded");
    } catch (e: any) {
      Alert.alert("Upload failed", e.message);
      setStatus("");
    }
  };

  const pickScreenshot = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Permission needed", "Please allow photo library access");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: "images",
      quality: 0.9,
    });
    if (result.canceled || !result.assets?.length) return;

    setStatus("Extracting stats from screenshot...");
    try {
      const data = await uploadScreenshot(result.assets[0].uri);
      if (data.workout_id) {
        setSelectedWorkout(data.workout_id);
        setScreenshotStats(data.extracted_stats);
        setStatus("✅ Stats extracted");
        Alert.alert(
          "Stats Extracted",
          `Shots: ${data.extracted_stats?.total_shots || "?"}\nHR: ${data.extracted_stats?.avg_heart_rate || "?"} bpm\nDistance: ${data.extracted_stats?.total_distance || "?"}m`
        );
      } else {
        setStatus("⚠️ Could not extract stats");
        Alert.alert("Notice", "Could not read stats from screenshot. You can still proceed without watch data.");
      }
    } catch (e: any) {
      setStatus("Screenshot upload failed");
    }
  };

  const handleStart = async () => {
    if (!videoId) { Alert.alert("Upload video first"); return; }
    try {
      const r = await startAnalysis(videoId, selectedWorkout || undefined);
      navigation.navigate("AnalysisProgress", { taskId: r.task_id });
    } catch (e: any) { Alert.alert("Failed", e.message); }
  };

  return (
    <View style={s.wrap}>
      <Text style={s.title}>Start Analysis</Text>

      <TouchableOpacity style={s.btn} onPress={pickVideo}>
        <Text style={s.btnT}>{videoId ? "✅ Video Ready" : "📹 Select Video"}</Text>
      </TouchableOpacity>
      {status ? <Text style={s.status}>{status}</Text> : null}

      <TouchableOpacity style={s.btn} onPress={pickScreenshot}>
        <Text style={s.btnT}>
          {screenshotStats ? `📊 ${screenshotStats.total_shots || "?"} shots | HR ${screenshotStats.avg_heart_rate || "?"}` : "📱 OPPO Screenshot (optional)"}
        </Text>
      </TouchableOpacity>

      <Text style={s.hint}>
        Take a screenshot of your OPPO Watch tennis mode summary.{"\n"}
        AI will extract your stats automatically.
      </Text>

      <TouchableOpacity style={[s.startBtn, !videoId && { opacity: 0.5 }]} onPress={handleStart} disabled={!videoId}>
        <Text style={s.startBtnT}>Start AI Analysis</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, padding: 16, backgroundColor: "#f5f5f5" },
  title: { fontSize: 22, fontWeight: "bold", marginTop: 40, marginBottom: 24 },
  btn: { backgroundColor: "#fff", borderRadius: 12, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: "#ddd" },
  btnT: { fontSize: 16, textAlign: "center" },
  status: { textAlign: "center", color: "#4CAF50", marginBottom: 8, fontSize: 13 },
  hint: { textAlign: "center", color: "#999", fontSize: 12, marginBottom: 16, lineHeight: 18 },
  startBtn: { backgroundColor: "#4CAF50", borderRadius: 12, padding: 18, alignItems: "center", marginTop: 8 },
  startBtnT: { color: "#fff", fontSize: 18, fontWeight: "600" },
});
