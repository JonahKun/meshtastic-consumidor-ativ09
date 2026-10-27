// Contagem de pacotes por no nas ultimas 48h, com separacao por salto (hops_away > 0).
// Uso:  mongosh "<MONGO_URI>/<MONGO_DB>" consultas/contagem_por_no_48h.js
// (nao coloque a senha em arquivos versionados; passe a URI pelo terminal)
// Somente leitura.
const horas = 48;
const corte = new Date(Date.now() - horas * 3600 * 1000);
const hops = "$mensagem.hops_away";

const resultado = db.getCollection("pacotes_brutos").aggregate([
  { $match: { recebido_em: { $gte: corte }, mensagem: { $exists: true } } },
  { $group: {
      _id: { $ifNull: ["$mensagem.from", "$mensagem.sender"] },   // no de origem
      total:     { $sum: 1 },
      diretos:   { $sum: { $cond: [{ $eq: [hops, 0] }, 1, 0] } },  // ouvidos direto pelo gateway
      por_salto: { $sum: { $cond: [{ $gt: [hops, 0] }, 1, 0] } },  // ouvidos por salto
      sem_info:  { $sum: { $cond: [{ $eq: [{ $ifNull: [hops, null] }, null] }, 1, 0] } },
      ultimo:    { $max: "$recebido_em" }
  } },
  { $sort: { total: -1 } }
]).toArray();

print(`Pacotes por no nas ultimas ${horas}h (corte UTC: ${corte.toISOString()})`);
printjson(resultado);
print(`nos distintos: ${resultado.length}  pacotes: ${resultado.reduce((a, r) => a + r.total, 0)}`);
