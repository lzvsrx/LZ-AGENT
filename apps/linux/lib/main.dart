import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

void main() => runApp(LzAgentApp(api: LocalAgentApi()));

abstract interface class AgentApi {
  Future<String> chat(String message, {required bool private});
}

class LocalAgentApi implements AgentApi {
  LocalAgentApi({this.endpoint = 'http://127.0.0.1:8765'});
  final String endpoint;

  @override
  Future<String> chat(String message, {required bool private}) async {
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 3);
    try {
      final request = await client.postUrl(Uri.parse('$endpoint/api/v1/chat'));
      request.headers.contentType = ContentType.json;
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
  final _message = TextEditingController();
  var _private = false;
  var _busy = false;
  var _state = 'Pronto';
  var _response = 'A resposta acessível aparecerá aqui.';

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
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
