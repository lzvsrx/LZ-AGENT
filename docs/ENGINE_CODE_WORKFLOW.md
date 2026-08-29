# Unity, Unreal e Godot como código

O LZ Agent não depende de edição manual em interfaces gráficas para produzir projetos de motores.
Código-fonte, cenas textuais, configurações, manifests, assets de origem e scripts de build devem ser
versionados e reproduzíveis por linha de comando.

- Godot: `.gd`, `.tscn`, `.tres` e `project.godot` como texto; build/teste pelo modo headless.
- Unity: C#, asmdefs, manifests e configurações no Git; validação/build em batch mode.
- Unreal: C++, Build.cs, Target.cs, `.uproject` e configurações no Git; build por UBT/UAT.
- Execuções passam por grants, checkpoint, timeout, logs e confirmação para publicação/sobrescrita.

Os motores continuam necessários como compilador/runtime dos próprios formatos. “Por programação”
significa resultado recriável por scripts e código versionado, sem etapas manuais ocultas no editor.
