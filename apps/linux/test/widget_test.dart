import 'package:flutter_test/flutter_test.dart';
import 'package:lz_agent_linux/main.dart';

class FakeApi implements AgentApi {
  @override
  Future<void> login(String username, String password) async {}

  @override
  Future<String> chat(String message, {required bool private}) async =>
      private ? 'Resposta privada' : 'Resposta auditada';
}

void main() {
  testWidgets('fluxo principal é operável e anuncia resposta', (tester) async {
    await tester.pumpWidget(LzAgentApp(api: FakeApi()));
    expect(find.text('Como posso ajudar?'), findsOneWidget);
    await tester.enterText(find.bySemanticsLabel('Sua solicitação'), 'Olá');
    await tester.tap(find.text('Enviar'));
    await tester.pumpAndSettle();
    expect(find.text('Resposta auditada'), findsOneWidget);
    expect(find.text('Estado: Concluído'), findsOneWidget);
  });

  testWidgets('mensagem vazia é rejeitada com linguagem clara', (tester) async {
    await tester.pumpWidget(LzAgentApp(api: FakeApi()));
    await tester.tap(find.text('Enviar'));
    await tester.pump();
    expect(
      find.text('Digite uma solicitação antes de enviar.'),
      findsOneWidget,
    );
  });
}
