"use client";

import { useEffect, useState } from "react";
import { Save, Eye, EyeOff, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getConfig, saveConfig } from "@/lib/api";

export default function SettingsPage() {
  const [endpoint, setEndpoint] = useState("https://api.openai.com/v1");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConfig().then((cfg) => {
      if (cfg) {
        setEndpoint(cfg.api_endpoint);
        setModel(cfg.model);
      }
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!endpoint || !apiKey || !model) {
      setError("All fields are required.");
      return;
    }
    try {
      setSaving(true);
      setError(null);
      await saveConfig({ api_endpoint: endpoint, api_key: apiKey, model });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-1">Settings</h1>
      <p className="text-muted-foreground text-sm mb-8">Configure your LLM provider</p>

      <Card>
        <CardHeader>
          <CardTitle>LLM Configuration</CardTitle>
          <CardDescription>
            Connect any OpenAI-compatible API (OpenAI, Anthropic, Ollama, Together AI, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">API Endpoint</label>
            <Input
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="https://api.openai.com/v1"
            />
            <p className="text-xs text-muted-foreground">Base URL (without /chat/completions)</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">API Key</label>
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">Stored encrypted. Leave blank to keep existing key.</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Model</label>
            <Input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gpt-4o"
            />
            <p className="text-xs text-muted-foreground">e.g. gpt-4o, claude-3-5-sonnet-20241022, llama3</p>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button onClick={handleSave} disabled={saving} className="w-full">
            {saving ? (
              "Saving..."
            ) : saved ? (
              <><CheckCircle className="h-4 w-4" /> Saved!</>
            ) : (
              <><Save className="h-4 w-4" /> Save Configuration</>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
