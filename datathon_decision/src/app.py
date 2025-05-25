import os
import logging
from flask import Flask, request
from flask_restx import Api, Resource, fields
from datathon_decision.src.model_utils import predict_pipeline

# Configuração de logging
os.makedirs("../../logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("../../logs/api.log")
    ]
)

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Datathon Decision API",
    description="""
API para matchmaking de candidatos e vagas usando IA.

**Principais features do modelo:**
- Nível profissional, acadêmico e inglês do candidato e da vaga
- Match de área de atuação
- Contagem de palavras-chave técnicas (Java, Python, SAP, etc.)
- Proxies de fit cultural (experiência em multinacional, startup, consultoria)
- Proxies de engajamento (comentário negativo, taxa de desistência histórica)
- Similaridade entre objetivo profissional e título da vaga
- Histórico de empregos

**Exemplo de payload válido:**
```
{
  "payload": {
    "situacao_candidado": "Contratado pela Decision",
    "perfil_vaga": {
      "nivel profissional": "Sênior",
      "nivel_academico": "Superior Completo",
      "nivel_ingles": "Avançado",
      "areas_atuacao": "TI - DEV",
      "competencia_tecnicas_e_comportamentais": "Java Python SQL"
    },
    "informacoes_basicas": {
      "vaga_sap": "Não",
      "titulo_vaga": "Dev Java Sr"
    },
    "informacoes_profissionais": {
      "nivel_profissional": "Sênior",
      "area_atuacao": "Desenvolvimento",
      "conhecimentos_tecnicos": "Java Spring",
      "objetivo_profissional": "Desenvolvedor Java"
    },
    "formacao_e_idiomas": {
      "nivel_academico": "Superior Completo",
      "nivel_ingles": "Avançado"
    },
    "cv_pt": "Experiencia com Java e Python",
    "comentario_prospect": "Candidato promissor",
    "data_candidatura_prospect": "01-01-2023",
    "ultima_atualizacao_prospect": "10-01-2023",
    "candidato_taxa_desistencia_historica_num": 0.1
  }
}
```

**Exemplo de resposta de sucesso:**
```
{
  "match_probability": 0.02
}
```

**Exemplo de resposta de erro:**
```
{
  "error": "Mensagem de erro explicativa"
}
```
    """,
    doc="/docs"
)

ns = api.namespace('api', description='Operações principais')

predict_input = api.model('PredictInput', {
    'payload': fields.Raw(
        description='Payload bruto do candidato/vaga', 
        required=True,
        example={
            "situacao_candidado": "Contratado pela Decision",
            "perfil_vaga": {
                "nivel profissional": "Sênior",
                "nivel_academico": "Superior Completo",
                "nivel_ingles": "Avançado",
                "areas_atuacao": "TI - DEV",
                "competencia_tecnicas_e_comportamentais": "Java Python SQL"
            },
            "informacoes_basicas": {
                "vaga_sap": "Não",
                "titulo_vaga": "Dev Java Sr"
            },
            "informacoes_profissionais": {
                "nivel_profissional": "Sênior",
                "area_atuacao": "Desenvolvimento",
                "conhecimentos_tecnicos": "Java Spring",
                "objetivo_profissional": "Desenvolvedor Java"
            },
            "formacao_e_idiomas": {
                "nivel_academico": "Superior Completo",
                "nivel_ingles": "Avançado"
            },
            "cv_pt": "Experiencia com Java e Python",
            "comentario_prospect": "Candidato promissor",
            "data_candidatura_prospect": "01-01-2023",
            "ultima_atualizacao_prospect": "10-01-2023",
            "candidato_taxa_desistencia_historica_num": 0.1
        }
    )
})

success_response = api.model('SuccessResponse', {
    'match_probability': fields.Float(description='Probabilidade de match (0 a 1)')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Mensagem de erro explicativa')
})

@ns.route('/health')
class Health(Resource):
    @api.doc(description="Verifica se a API está ativa.")
    def get(self):
        logging.info("Health check called.")
        return {"status": "healthy"}

@ns.route('/predict')
class Predict(Resource):
    @api.expect(predict_input)
    @api.response(200, 'Sucesso', success_response)
    @api.response(400, 'Erro de validação ou processamento', error_response)
    @api.doc(description="Endpoint de predição real. Envie um JSON bruto de candidato/vaga.")
    def post(self):
        data = api.payload
        logging.info(f"/predict chamado. Dados recebidos: {data}")
        try:
            payload = data.get('payload', data)  # Permite tanto {payload: ...} quanto o dicionário direto
            prob = predict_pipeline(payload)
            logging.info(f"Probabilidade de match retornada: {prob}")
            return {"match_probability": prob}
        except Exception as e:
            logging.error(f"Erro na predição: {e}", exc_info=True)
            return {"error": str(e)}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True) 