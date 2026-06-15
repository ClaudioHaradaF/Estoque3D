import enum


class FormaPagamento(str, enum.Enum):
    DINHEIRO = 'dinheiro'
    CREDITO = 'credito'
    DEBITO = 'debito'
    PIX = 'pix'


class TipoMeta(str, enum.Enum):
    DIARIA = 'diaria'
    SEMANAL = 'semanal'
    MENSAL = 'mensal'
    ANUAL = 'anual'
    AVULSA = 'avulsa'


class CategoriaMeta(str, enum.Enum):
    FINANCEIRO = 'financeiro'
    INVESTIMENTO = 'investimento'
    FEIRA = 'feira'
    OUTRO = 'outro'