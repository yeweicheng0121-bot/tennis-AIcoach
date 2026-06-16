import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";
import { uploadVideo, listWorkouts, startAnalysis } from "../services/api";

export default function UploadScreen({ navigation }: any) {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [selectedWorkout, setSelectedWorkout] = useState<string | null>(null);
  const [workouts, setWorkouts] = useState<any[]>([]);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);

  const pickVideo = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: "video/*", copyToCacheDirectory: true });
    if (result.canceled || !result.assets?.length) return;
    const asset = result.assets[0];

    setStatus("Compressing...");
    setProgress(0);

    // Compress
    const outPath = `${FileSystem.cacheDirectory}comp_${Date.now()}.mp4`;
    try {
      const { FFmpegKit } = require("ffmpeg-kit-react-native");
      await FFmpegKit.execute(`-i ${asset.uri} -vf "scale=-2:720,fps=30" -c:v libx264 -b:v 4M -c:a aac -b:a 128k -y ${outPath}`);
    } catch {}

    // Upload
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

  const loadWorkouts = async () => {
    const list = await listWorkouts();
    setWorkouts(list);
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
      {status ? <Text style={s.status}>{status} {progress > 0 ? `${Math.round(progress * 100)}%` : ""}</Text> : null}
      <TouchableOpacity style={s.btn} onPress={loadWorkouts}>
        <Text style={s.btnT}>⌚ Select OPPO Workout</Text>
      </TouchableOpacity>
      {workouts.map(w => (
        <TouchableOpacity key={w.workout_id} style={[s.wItem, selectedWorkout === w.workout_id && s.wSel]} onPress={() => setSelectedWorkout(w.workout_id)}>
          <Text>{w.start_time} | {w.total_shots} shots | HR {w.avg_heart_rate}</Text>
        </TouchableOpacity>
      ))}
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
  status: { textAlign: "center", color: "#4CAF50", marginBottom: 8 },
  wItem: { padding: 14, backgroundColor: "#fff", marginBottom: 8, borderRadius: 8 },
  wSel: { borderWidth: 2, borderColor: "#4CAF50" },
  startBtn: { backgroundColor: "#4CAF50", borderRadius: 12, padding: 18, alignItems: "center", marginTop: 24 },
  startBtnT: { color: "#fff", fontSize: 18, fontWeight: "600" },
});
