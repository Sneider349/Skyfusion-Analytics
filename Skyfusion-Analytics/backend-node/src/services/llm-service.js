'use strict';

class LLMService {
  constructor() {
    this.provider = null;
    this.config = {};
    this.isInitialized = false;
  }

  async initialize(provider = 'openai') {
    this.provider = provider;
    this.config = {
      apiKey: process.env[`${provider.toUpperCase()}_API_KEY`] || process.env.OPENAI_API_KEY,
      baseUrl: process.env[`${provider.toUpperCase()}_BASE_URL`] || 'https://api.openai.com/v1'
    };

    if (!this.config.apiKey) {
      console.warn('[LLMService] No API key found. Using mock responses.');
    }

    this.isInitialized = true;
    console.log(`[LLMService] Initialized with provider: ${provider}`);
  }

  async generate(params) {
    if (!this.isInitialized) {
      throw new Error('LLM Service not initialized. Call initialize() first.');
    }

    switch (this.provider) {
      case 'openai':
        return this._generateOpenAI(params);
      case 'anthropic':
        return this._generateAnthropic(params);
      case 'local':
        return this._generateLocal(params);
      default:
        return this._generateMock(params);
    }
  }

  async _generateOpenAI(params) {
    if (!this.config.apiKey) {
      return this._generateMock(params);
    }

    const { prompt, model = 'gpt-4', temperature = 0.3, max_tokens = 2000 } = params;

    try {
      const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: prompt }],
          temperature,
          max_tokens
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status}`);
      }

      const data = await response.json();
      return {
        text: data.choices[0]?.message?.content || '',
        usage: data.usage,
        model: data.model
      };
    } catch (error) {
      console.error('[LLMService] OpenAI generation failed:', error);
      throw error;
    }
  }

  async _generateAnthropic(params) {
    const { prompt, model = 'claude-3-sonnet-20240229', temperature = 0.3, max_tokens = 2000 } = params;

    if (!this.config.apiKey) {
      return this._generateMock(params);
    }

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.config.apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: prompt }],
          temperature,
          max_tokens
        })
      });

      if (!response.ok) {
        throw new Error(`Anthropic API error: ${response.status}`);
      }

      const data = await response.json();
      return {
        text: data.content[0]?.text || '',
        usage: data.usage,
        model: data.model
      };
    } catch (error) {
      console.error('[LLMService] Anthropic generation failed:', error);
      throw error;
    }
  }

  async _generateLocal(params) {
    const { prompt, max_tokens = 2000 } = params;
    const localUrl = process.env.LOCAL_LLM_URL || 'http://localhost:11434/api/generate';

    try {
      const response = await fetch(localUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          stream: false,
          options: { num_predict: max_tokens }
        })
      });

      if (!response.ok) {
        throw new Error(`Local LLM error: ${response.status}`);
      }

      const data = await response.json();
      return { text: data.response || '' };
    } catch (error) {
      console.error('[LLMService] Local LLM failed:', error);
      return this._generateMock(params);
    }
  }

  _generateMock(params) {
    console.log('[LLMService] Using mock response');
    return {
      text: `
# Informe Técnico - Cuenca del Río Combeima

## Resumen Ejecutivo
El análisis morfológico y las predicciones de caudal indican condiciones **estables** 
para la cuenca del río Combeima en el período evaluado.

## Análisis de Vegetación (NDVI)
- **Índice actual**: 0.65 (vegetación saludable)
- **Tendencia**: Estable respecto al período anterior
- **Cobertura vegetal**: 78% del área analizada

## Análisis de Cuerpos de Agua (NDWI)
- **Índice actual**: 0.18 (niveles normales)
- **Distribución**: Concentrada en el cauce principal
- **Alerta**: Ninguna condición anómala detectada

## Proyecciones de Caudal
| Período | Caudal (m³/s) | Confianza |
|---------|---------------|-----------|
| 6 horas | 8.5 | 95% |
| 12 horas | 9.2 | 92% |
| 24 horas | 10.1 | 88% |

## Conclusiones
1. No se prevén eventos de inundación en las próximas 24 horas
2. Los índices de vegetación indican buena salud del ecosistema
3. Se recomienda monitoreo continuo ante posibles cambios

---
*Informe generado automáticamente*
      `.trim(),
      mock: true
    };
  }

  getStatus() {
    return {
      initialized: this.isInitialized,
      provider: this.provider,
      hasApiKey: !!this.config.apiKey
    };
  }
}

module.exports = new LLMService();
