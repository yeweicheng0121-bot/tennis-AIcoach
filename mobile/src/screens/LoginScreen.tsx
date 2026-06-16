import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { login, register, getProfile } from "../services/api";
import { saveToken } from "../services/auth";
import { useStore } from "../store/useStore";

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
    <View style={s.container}>
      <Text style={s.title}>🎾 AI Tennis Coach</Text>
      <TextInput style={s.input} placeholder="Phone" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
      <TextInput style={s.input} placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
      <TouchableOpacity style={s.btn} onPress={handleSubmit}>
        <Text style={s.btnText}>{isRegisterMode ? "Register" : "Login"}</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => setIsRegisterMode(!isRegisterMode)}>
        <Text style={s.switch}>{isRegisterMode ? "Have account? Login" : "No account? Register"}</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#fff" },
  title: { fontSize: 28, fontWeight: "bold", textAlign: "center", marginBottom: 40 },
  input: { borderWidth: 1, borderColor: "#ddd", borderRadius: 8, padding: 14, fontSize: 16, marginBottom: 16 },
  btn: { backgroundColor: "#4CAF50", borderRadius: 8, padding: 16, alignItems: "center" },
  btnText: { color: "#fff", fontSize: 18, fontWeight: "600" },
  switch: { textAlign: "center", marginTop: 16, color: "#4CAF50" },
});
