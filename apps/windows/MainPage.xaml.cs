using System.Net.Http.Json;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation.Peers;
using Microsoft.UI.Xaml.Controls;

namespace LzAgent_Windows;

public sealed partial class MainPage : Page
{
    private static readonly HttpClient Api = new() { BaseAddress = new Uri("http://127.0.0.1:8765") };
    public MainPage() => InitializeComponent();

    private async void SendButton_Click(object sender, RoutedEventArgs e)
    {
        var message = MessageInput.Text.Trim();
        if (string.IsNullOrWhiteSpace(message))
        {
            Announce("Digite uma solicitação antes de enviar.", "Estado: atenção");
            MessageInput.Focus(FocusState.Keyboard);
            return;
        }
        SendButton.IsEnabled = false;
        Announce("Processando…", "Estado: pensando");
        try
        {
            using var response = await Api.PostAsJsonAsync("/api/v1/chat", new ChatRequest(message, PrivateMode.IsChecked is true));
            response.EnsureSuccessStatusCode();
            var payload = await response.Content.ReadFromJsonAsync<ChatResponse>();
            Announce(payload?.Text ?? "Resposta vazia.", "Estado: concluído");
        }
        catch (HttpRequestException)
        {
            Announce("O serviço local não está disponível. Inicie o núcleo com lz-agent.", "Estado: offline");
        }
        finally { SendButton.IsEnabled = true; }
    }

    private void Navigation_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.IsSettingsSelected) Announce("Configurações do LZ Agent.", "Configurações");
        else if (args.SelectedItemContainer?.Tag is string tag && tag != "home")
            Announce($"Área {args.SelectedItemContainer.Content} conectada ao contrato {tag}.", "Navegação");
    }

    private void Announce(string text, string state)
    {
        ResponseText.Text = text;
        AgentState.Text = state;
        FrameworkElementAutomationPeer.FromElement(ResponseText)?.RaiseAutomationEvent(AutomationEvents.LiveRegionChanged);
    }

    private sealed record ChatRequest(string Message, bool Private);
    private sealed record ChatResponse(string Text, string Provider, string Model, bool Offline);
}
