import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

void main() => runApp(LzAgentApp(api: LocalAgentApi()));

abstract interface class AgentApi {
  Future<void> login(String username, String password);
  Future<String> chat(String message, {required bool private});
}

class LocalAgentApi implements AgentApi {
  LocalAgentApi({this.endpoint = 'http://127.0.0.1:8765'});
  final String endpoint;
  String? _accessToken;

  @override
  Future<void> login(String username, String password) async {
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 3);
    try {
      final request = await client.postUrl(Uri.parse('$endpoint/api/v1/auth/login'));
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode({'username': username, 'password': password}));
      final response = await request.close();
      final body = await utf8.decoder.bind(response).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw const HttpException('Credenciais inválidas ou núcleo indisponível.');
      }
      _accessToken = (jsonDecode(body) as Map<String, dynamic>)['access_token'] as String;
    } finally {
      client.close(force: true);
    }
  }

  @override
  Future<String> chat(String message, {required bool private}) async {
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 3);
    try {
      final request = await client.postUrl(Uri.parse('$endpoint/api/v1/chat'));
      request.headers.contentType = ContentType.json;
      if (_accessToken != null) {
        request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $_accessToken');
      }
      request.write(jsonEncode({'message': message, 'private': private}));
      final response = await request.close();
      final body = await utf8.decoder.bind(response).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw const HttpException('Resposta inválida do núcleo local.');
      }
      return (jsonDecode(body) as Map<String, dynamic>)['text'] as String;
    } finally {
      client.close(force: true);
    }
  }
}

class LzAgentApp extends StatelessWidget {
  const LzAgentApp({required this.api, super.key});
  final AgentApi api;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'LZ Agent',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF00CBEF),
        brightness: Brightness.dark,
      ),
      useMaterial3: true,
      visualDensity: VisualDensity.standard,
    ),
    home: AgentHome(api: api),
  );
}

class AgentHome extends StatefulWidget {
  const AgentHome({required this.api, super.key});
  final AgentApi api;

  @override
  State<AgentHome> createState() => _AgentHomeState();
}

class _AgentHomeState extends State<AgentHome> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  final _message = TextEditingController();
  var _private = false;
  var _busy = false;
  var _state = 'Pronto';
  var _response = 'A resposta acessível aparecerá aqui.';

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _message.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _busy = true;
      _state = 'Autenticando';
    });
    try {
      await widget.api.login(_username.text.trim(), _password.text);
      if (!mounted) return;
      _password.clear();
      setState(() {
        _state = 'Autenticado';
        _response = 'Login concluído para esta sessão do aplicativo.';
      });
    } on Object {
      if (!mounted) return;
      setState(() {
        _state = 'Não autenticado';
        _response = 'Não foi possível entrar. Verifique usuário, senha e núcleo local.';
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _send() async {
    final text = _message.text.trim();
    if (text.isEmpty) {
      setState(() {
        _state = 'Atenção';
        _response = 'Digite uma solicitação antes de enviar.';
      });
      return;
    }
    setState(() {
      _busy = true;
      _state = 'Pensando';
      _response = 'Processando…';
    });
    try {
      final response = await widget.api.chat(text, private: _private);
      if (!mounted) return;
      setState(() {
        _state = 'Concluído';
        _response = response;
      });
    } on Object {
      if (!mounted) return;
      setState(() {
        _state = 'Offline';
        _response = 'O núcleo local não está disponível. Inicie lz-agent e tente novamente.';
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('LZ Agent'), centerTitle: false),
    drawer: NavigationDrawer(
      children: const [
        DrawerHeader(child: Text('Seu agente pessoal inteligente')),
        NavigationDrawerDestination(
          icon: Icon(Icons.home_outlined),
          label: Text('Home'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.task_outlined),
          label: Text('Tarefas'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.build_outlined),
          label: Text('Ferramentas'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.memory_outlined),
          label: Text('Memória'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.accessibility_new),
          label: Text('Acessibilidade'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.devices_outlined),
          label: Text('Dispositivos'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.code),
          label: Text('Desenvolvedor'),
        ),
      ],
    ),
    body: SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 840),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Semantics(
                liveRegion: true,
                label: 'Estado do agente: $_state',
                child: Text(
                  'Estado: $_state',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Como posso ajudar?',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _username,
                autofillHints: const [AutofillHints.username],
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Usuário',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _password,
                obscureText: true,
                autofillHints: const [AutofillHints.password],
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Senha',
                ),
              ),
              const SizedBox(height: 12),
              Align(
                alignment: Alignment.centerLeft,
                child: OutlinedButton(
                  onPressed: _busy ? null : _login,
                  child: const Text('Entrar'),
                ),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _message,
                minLines: 4,
                maxLines: 10,
                textInputAction: TextInputAction.newline,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Sua solicitação',
                  hintText: 'Digite uma tarefa…',
                ),
              ),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                value: _private,
                onChanged: (value) => setState(() => _private = value ?? false),
                title: const Text('Sessão privada'),
                subtitle: const Text(
                  'O conteúdo desta conversa não será salvo.',
                ),
                controlAffinity: ListTileControlAffinity.leading,
              ),
              Align(
                alignment: Alignment.centerLeft,
                child: FilledButton.icon(
                  onPressed: _busy ? null : _send,
                  icon: _busy
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                  label: const Text('Enviar'),
                ),
              ),
              const SizedBox(height: 20),
              Semantics(
                liveRegion: true,
                label: 'Resposta do LZ Agent: $_response',
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: SelectableText(_response),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
