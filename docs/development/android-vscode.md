# Android pelo VS Code, sem Android Studio

O aplicativo Android é um projeto nativo Kotlin/Jetpack Compose. Android Studio é opcional e não participa do build documentado.

## Pré-requisitos

- VS Code com as extensões recomendadas pelo workspace;
- JDK 17;
- Android Command-line Tools e Platform Tools;
- um dispositivo Android com depuração USB ou um emulador iniciado externamente.

Execute `scripts/setup-android.ps1` no terminal PowerShell. O script aceita licenças, instala API 36 e Build Tools 36 e cria o `local.properties` local, que nunca é versionado.

## Fluxo diário

1. Execute a tarefa `LZ: iniciar núcleo local`.
2. Conecte o aparelho e execute `Android: listar dispositivos`.
3. Execute `Android: encaminhar API local (adb reverse)`.
4. Execute `Android: compilar e instalar debug`.

O `adb reverse tcp:8765 tcp:8765` permite que `127.0.0.1:8765` no aparelho acesse o núcleo no computador. O tráfego HTTP sem TLS existe somente para essa conexão local de desenvolvimento; uma implantação remota deve usar HTTPS.

## Terminal

```powershell
cd apps/android
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug
adb reverse tcp:8765 tcp:8765
.\gradlew.bat installDebug
```

O APK fica em `apps/android/app/build/outputs/apk/debug/app-debug.apk`.
