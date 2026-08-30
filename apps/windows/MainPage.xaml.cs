using System.Net.Http.Json;
using System.Net.Http.Headers;
using System.Text.Json.Serialization;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation.Peers;
using Microsoft.UI.Xaml.Controls;

namespace LzAgent_Windows;

public sealed partial class MainPage : Page
{
    private static readonly HttpClient Api = new() { BaseAddress = new Uri("http://127.0.0.1:8765") };
    private string? accessToken;
    public MainPage() => InitializeComponent();

    private async void LoginButton_Click(object sender, RoutedEventArgs e)
    {
        LoginButton.IsEnabled = false;
        try
        {
            using var response = await Api.PostAsJsonAsync("/api/v1/auth/login", new LoginRequest(UsernameInput.Text.Trim(), PasswordInput.Password));
            response.EnsureSuccessStatusCode();
            var session = await response.Content.ReadFromJsonAsync<LoginResponse>();
            accessToken = session?.AccessToken;
            PasswordInput.Password = "";
            Announce("Login concluído para esta sessão do aplicativo.", "Estado: autenticado");
        }
        catch (HttpRequestException)
        {
            Announce("Não foi possível entrar. Verifique usuário, senha e núcleo local.", "Estado: não autenticado");
        }
        finally { LoginButton.IsEnabled = true; }
    }

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
            using var request = new HttpRequestMessage(HttpMethod.Post, "/api/v1/chat")
            {
                Content = JsonContent.Create(new ChatRequest(message, PrivateMode.IsChecked is true)),
            };
            if (accessToken is not null)
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
            using var response = await Api.SendAsync(request);
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
    private sealed record LoginRequest(string Username, string Password);
    private sealed record LoginResponse([property: JsonPropertyName("access_token")] string AccessToken);
}
