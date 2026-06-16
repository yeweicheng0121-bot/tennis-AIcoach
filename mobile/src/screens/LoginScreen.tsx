import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform } from "react-native";
import { login, register, getProfile } from "../services/api";
import { saveToken } from "../services/auth";
import { useStore } from "../store/useStore";

const COLORS = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", border: "#1F2937", input: "#1A1F2E" };

export default function LoginScreen() {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const setUser = useStore((s) => s.setUser);

  const handleSubmit = async () => {
    try {
      const fn = isRegisterMode ? register : login;
      const result = await fn(phone, password);
      await saveToken(result.access_token, result.user_id);
      const profile = await getProfile();
      setUser(profile);
    } catch (e: any) {
      Alert.alert("Error", e.response?.data?.detail || e.message);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>🎾</Text>
        <Text style={styles.title}>AI Coach</Text>
        <Text style={styles.subtitle}>Your personal tennis analyst</Text>
      </View>
      <View style={styles.form}>
        <TextInput style={styles.input} placeholder="Phone" placeholderTextColor={COLORS.muted} value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <TextInput style={styles.input} placeholder="Password" placeholderTextColor={COLORS.muted} value={password} onChangeText={setPassword} secureTextEntry />
        <TouchableOpacity style={styles.button} onPress={handleSubmit} activeOpacity={0.8}>
          <Text style={styles.buttonText}>{isRegisterMode ? "Create Account" : "Sign In"}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setIsRegisterMode(!isRegisterMode)}>
          <Text style={styles.switch}>{isRegisterMode ? "Already have an account? Sign in" : "New here? Create account"}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 28, backgroundColor: COLORS.bg },
  header: { alignItems: "center", marginBottom: 48 },
  logo: { fontSize: 56, marginBottom: 12 },
  title: { fontSize: 32, fontWeight: "800", color: COLORS.text, letterSpacing: -0.5 },
  subtitle: { fontSize: 14, color: COLORS.muted, marginTop: 6 },
  form: {},
  input: { backgroundColor: COLORS.input, borderRadius: 14, padding: 16, fontSize: 16, color: COLORS.text, marginBottom: 14, borderWidth: 1, borderColor: COLORS.border },
  button: { backgroundColor: COLORS.accent, borderRadius: 14, padding: 17, alignItems: "center", marginTop: 6 },
  buttonText: { color: "#0A0D14", fontSize: 17, fontWeight: "700" },
  switch: { textAlign: "center", marginTop: 20, color: COLORS.muted, fontSize: 13 },
});
