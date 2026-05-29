// Mensagem simples
console.log("Sistema carregado!");

// Confirma exclusão
function confirmarExclusao() {
    return confirm("Deseja excluir?");
}

// Busca o gráfico
const ctx = document.getElementById('grafico');

if (ctx) {

    // Dados vindos do Flask
    const produtos = ctx.dataset.produtos;
    const clientes = ctx.dataset.clientes;
    const vendas = ctx.dataset.vendas;

    // Cria gráfico
    new Chart(ctx, {

        type: 'bar',

        data: {

            labels: ['Produtos', 'Clientes', 'Vendas'],

            datasets: [{

                label: 'Dados do Sistema',

                data: [produtos, clientes, vendas],

                borderWidth: 1

            }]
        }
    });
}