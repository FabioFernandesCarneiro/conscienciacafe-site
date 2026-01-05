import React from 'react';
import { ArrowLeft, Search, Plus, MoreVertical, Filter, Package, Save, Trash2, Eye, Coffee, X } from 'lucide-react';

const ProductManagementScreen = () => {
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Status Bar */}
      <div className="w-full p-2 flex justify-between text-xs bg-white border-b border-gray-200">
        <span>9:41</span>
        <div className="flex space-x-2">
          <span>Wi-Fi</span>
          <span>100%</span>
        </div>
      </div>

      {/* App Bar */}
      <div className="w-full px-4 py-3 flex justify-between items-center bg-white border-b border-gray-200">
        <div className="flex items-center">
          <ArrowLeft size={20} className="mr-2" />
          <h1 className="text-lg font-semibold">Produtos</h1>
        </div>
        <div className="flex">
          <button className="p-2 bg-gray-100 rounded-full mr-2">
            <Filter size={18} className="text-gray-600" />
          </button>
          <button className="p-2 bg-gray-100 rounded-full">
            <MoreVertical size={18} className="text-gray-600" />
          </button>
        </div>
      </div>

      {/* Pesquisa e categorias */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex mb-4">
          <div className="flex-1 flex items-center bg-gray-100 rounded-lg px-3 py-2">
            <Search size={18} className="text-gray-400 mr-2" />
            <input 
              type="text" 
              placeholder="Buscar produto..."
              className="bg-transparent w-full focus:outline-none text-sm"
            />
          </div>
        </div>
        
        {/* Categorias Tabs */}
        <div className="flex overflow-x-auto border-b border-gray-200 pb-1">
          <button className="px-4 py-2 text-sm font-medium text-green-500 border-b-2 border-green-500 flex-shrink-0">
            Todos (35)
          </button>
          <button className="px-4 py-2 text-sm text-gray-500 flex-shrink-0">
            Cafés (12)
          </button>
          <button className="px-4 py-2 text-sm text-gray-500 flex-shrink-0">
            Bebidas (8)
          </button>
          <button className="px-4 py-2 text-sm text-gray-500 flex-shrink-0">
            Comidas (10)
          </button>
          <button className="px-4 py-2 text-sm text-gray-500 flex-shrink-0">
            Acessórios (5)
          </button>
        </div>
      </div>

      {/* Lista de produtos */}
      <div className="flex-1 overflow-auto">
        <div className="p-4 space-y-3">
          {/* Café Especial */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 flex justify-between items-start">
              <div className="flex">
                <div className="w-16 h-16 bg-amber-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                  <Coffee size={24} className="text-amber-600" />
                </div>
                <div>
                  <h3 className="font-medium">Etiópia Yirgacheffe</h3>
                  <div className="flex items-center mt-1">
                    <div className="bg-amber-50 text-amber-700 text-xs px-2 py-0.5 rounded-full">
                      Café
                    </div>
                    <span className="text-xs text-gray-500 ml-2">ID: #1001</span>
                  </div>
                  <div className="mt-2">
                    <span className="font-semibold">R$ 12,00</span>
                    <span className="text-xs text-gray-500 ml-2">Disponível</span>
                  </div>
                </div>
              </div>
              <button className="text-gray-400">
                <Eye size={18} />
              </button>
            </div>
            
            {/* Atributos */}
            <div className="px-4 pb-4">
              <div className="text-xs text-gray-500 mb-2">Atributos específicos:</div>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Pontuação: 86</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Fazenda: Idido</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Processo: Lavado</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Perfil: Floral</span>
              </div>
            </div>
          </div>
          
          {/* Bebida */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 flex justify-between items-start">
              <div className="flex">
                <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                  <span className="text-blue-600 text-2xl">☕</span>
                </div>
                <div>
                  <h3 className="font-medium">Cappuccino</h3>
                  <div className="flex items-center mt-1">
                    <div className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                      Bebida
                    </div>
                    <span className="text-xs text-gray-500 ml-2">ID: #2005</span>
                  </div>
                  <div className="mt-2">
                    <span className="font-semibold">R$ 9,50</span>
                    <span className="text-xs text-gray-500 ml-2">Disponível</span>
                  </div>
                </div>
              </div>
              <button className="text-gray-400">
                <Eye size={18} />
              </button>
            </div>
            
            {/* Atributos */}
            <div className="px-4 pb-4">
              <div className="text-xs text-gray-500 mb-2">Atributos específicos:</div>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Tamanhos: P/M/G</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Opções de leite: 3</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Tempo de preparo: 5min</span>
              </div>
            </div>
          </div>
          
          {/* Comida */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 flex justify-between items-start">
              <div className="flex">
                <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                  <span className="text-purple-600 text-2xl">🥪</span>
                </div>
                <div>
                  <h3 className="font-medium">Waffle de Pão de Queijo</h3>
                  <div className="flex items-center mt-1">
                    <div className="bg-purple-50 text-purple-700 text-xs px-2 py-0.5 rounded-full">
                      Comida
                    </div>
                    <span className="text-xs text-gray-500 ml-2">ID: #3015</span>
                  </div>
                  <div className="mt-2">
                    <span className="font-semibold">R$ 20,00</span>
                    <span className="text-xs text-gray-500 ml-2">Disponível</span>
                  </div>
                </div>
              </div>
              <button className="text-gray-400">
                <Eye size={18} />
              </button>
            </div>
            
            {/* Atributos */}
            <div className="px-4 pb-4">
              <div className="text-xs text-gray-500 mb-2">Atributos específicos:</div>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Porção: 2 pessoas</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Proteínas: 4 opções</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Acompanhamentos: Sim</span>
              </div>
            </div>
          </div>
          
          {/* Acessório */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 flex justify-between items-start">
              <div className="flex">
                <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                  <Package size={24} className="text-gray-600" />
                </div>
                <div>
                  <h3 className="font-medium">Prensa Francesa 350ml</h3>
                  <div className="flex items-center mt-1">
                    <div className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">
                      Acessório
                    </div>
                    <span className="text-xs text-gray-500 ml-2">ID: #4008</span>
                  </div>
                  <div className="mt-2">
                    <span className="font-semibold">R$ 89,90</span>
                    <span className="text-xs text-gray-500 ml-2">Estoque: 6</span>
                  </div>
                </div>
              </div>
              <button className="text-gray-400">
                <Eye size={18} />
              </button>
            </div>
            
            {/* Atributos */}
            <div className="px-4 pb-4">
              <div className="text-xs text-gray-500 mb-2">Atributos específicos:</div>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Material: Vidro/Inox</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Capacidade: 350ml</span>
                <span className="bg-gray-50 text-gray-700 text-xs px-2 py-1 rounded-full">Marca: Hario</span>
              </div>
            </div>
          </div>
          
          {/* Produto Indisponível */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden opacity-60">
            <div className="p-4 flex justify-between items-start">
              <div className="flex">
                <div className="w-16 h-16 bg-red-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                  <Coffee size={24} className="text-red-600" />
                </div>
                <div>
                  <h3 className="font-medium">Colômbia Supremo</h3>
                  <div className="flex items-center mt-1">
                    <div className="bg-red-50 text-red-700 text-xs px-2 py-0.5 rounded-full">
                      Indisponível
                    </div>
                    <span className="text-xs text-gray-500 ml-2">ID: #1005</span>
                  </div>
                  <div className="mt-2">
                    <span className="font-semibold">R$ 11,50</span>
                    <span className="text-xs text-red-500 ml-2">Fora de estoque</span>
                  </div>
                </div>
              </div>
              <button className="text-gray-400">
                <Eye size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Botão de adicionar */}
      <div className="p-4 bg-white border-t border-gray-200">
        <button className="w-full p-3 bg-green-500 text-white font-medium rounded-lg flex items-center justify-center">
          <Plus size={18} className="mr-2" />
          <span>Adicionar Novo Produto</span>
        </button>
      </div>
    </div>
  );
};

export default ProductManagementScreen;
