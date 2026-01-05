import React from 'react';
import { ArrowLeft, Save, X, Plus, Minus, Upload, Coffee, Edit } from 'lucide-react';

const ProductEditScreen = () => {
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
          <h1 className="text-lg font-semibold">Editar Produto</h1>
        </div>
        <div className="flex">
          <button className="p-2 bg-green-100 rounded-full">
            <Save size={18} className="text-green-600" />
          </button>
        </div>
      </div>

      {/* Conteúdo do formulário */}
      <div className="flex-1 overflow-auto p-4">
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <div className="flex items-center mb-4">
            <div className="w-20 h-20 bg-amber-100 rounded-lg flex items-center justify-center mr-4 flex-shrink-0 relative">
              <Coffee size={32} className="text-amber-600" />
              <div className="absolute -bottom-2 -right-2 p-1 bg-white rounded-full shadow-sm">
                <Edit size={14} className="text-gray-600" />
              </div>
            </div>
            <div>
              <h2 className="font-semibold mb-1">Foto do Produto</h2>
              <p className="text-sm text-gray-500">Toque na imagem para alterar</p>
              <button className="mt-2 text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full flex items-center">
                <Upload size={12} className="mr-1" />
                <span>Enviar imagem</span>
              </button>
            </div>
          </div>
          
          <div className="mb-4">
            <div className="flex justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">Nome do Produto *</label>
              <span className="text-xs text-gray-500">4/50</span>
            </div>
            <input 
              type="text" 
              value="Café"
              className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Nome do produto"
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Categoria *</label>
            <div className="relative">
              <select className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none">
                <option value="cafe">Café</option>
                <option value="bebida">Bebida</option>
                <option value="comida">Comida</option>
                <option value="acessorio">Acessório</option>
              </select>
              <div className="absolute top-1/2 right-3 transform -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
            <textarea 
              className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 min-h-20"
              placeholder="Descrição do produto"
              rows="3"
            >Café espresso tradicional de alta qualidade.</textarea>
          </div>
          
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Preço (R$) *</label>
              <input 
                type="text" 
                value="6,00"
                className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="0,00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Código (SKU)</label>
              <input 
                type="text" 
                value="ESP001"
                className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Código do produto"
              />
            </div>
          </div>
          
          <div className="mb-4">
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm font-medium text-gray-700">Disponibilidade</label>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">Indisponível</span>
                <div className="relative w-10 h-6 bg-green-500 rounded-full">
                  <div className="absolute w-4 h-4 bg-white rounded-full top-1 right-1"></div>
                </div>
                <span className="text-xs text-gray-500">Disponível</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Atributos específicos por categoria */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-semibold">Atributos de Café</h2>
            <button className="text-xs bg-green-100 text-green-600 px-3 py-1 rounded-full flex items-center">
              <Plus size={12} className="mr-1" />
              <span>Adicionar</span>
            </button>
          </div>
          
          {/* Origem */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Origem</label>
            <div className="relative">
              <select className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none">
                <option value="brasil">Brasil</option>
                <option value="colombia">Colômbia</option>
                <option value="etiopia" selected>Etiópia</option>
                <option value="guatemala">Guatemala</option>
                <option value="quenia">Quênia</option>
              </select>
              <div className="absolute top-1/2 right-3 transform -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
          </div>
          
          {/* Fazenda */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Fazenda/Cooperativa</label>
            <input 
              type="text" 
              value="Idido"
              className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Nome da fazenda ou cooperativa"
            />
          </div>
          
          {/* Altitude */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Altitude</label>
            <input 
              type="text" 
              value="1.800 - 2.000m"
              className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Altitude de cultivo"
            />
          </div>
          
          {/* Variedade */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Variedade</label>
            <input 
              type="text" 
              value="Heirloom"
              className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Variedade do café"
            />
          </div>
          
          {/* Processo */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Processo</label>
            <div className="relative">
              <select className="w-full p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none">
                <option value="natural">Natural</option>
                <option value="lavado" selected>Lavado</option>
                <option value="honey">Honey</option>
                <option value="fermentado">Fermentado</option>
              </select>
              <div className="absolute top-1/2 right-3 transform -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
          </div>
          
          {/* Pontuação */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Pontuação (SCA)</label>
            <div className="flex items-center">
              <input 
                type="text" 
                value="86"
                className="w-20 p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 text-center"
              />
              <input
                type="range"
                min="80" 
                max="100"
                value="86"
                className="flex-1 ml-4 accent-green-500"
              />
            </div>
          </div>
          
          {/* Perfil Sensorial */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Perfil Sensorial</label>
            <div className="flex flex-wrap gap-2 mb-2">
              <div className="flex items-center bg-amber-50 text-amber-700 px-2 py-1 rounded-full text-xs">
                <span>Floral</span>
                <button className="ml-1 text-amber-500">
                  <X size={12} />
                </button>
              </div>
              <div className="flex items-center bg-amber-50 text-amber-700 px-2 py-1 rounded-full text-xs">
                <span>Cítrico</span>
                <button className="ml-1 text-amber-500">
                  <X size={12} />
                </button>
              </div>
              <div className="flex items-center bg-amber-50 text-amber-700 px-2 py-1 rounded-full text-xs">
                <span>Mel</span>
                <button className="ml-1 text-amber-500">
                  <X size={12} />
                </button>
              </div>
            </div>
            <div className="flex">
              <input 
                type="text" 
                placeholder="Adicionar nota sensorial"
                className="flex-1 p-2 border border-gray-200 rounded-l-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button className="bg-green-500 text-white px-3 rounded-r-lg flex items-center">
                <Plus size={16} />
              </button>
            </div>
          </div>
        </div>
        
        {/* Centro de custo / Ambiente */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h2 className="font-semibold mb-4">Centro de Custo</h2>
          
          <div className="space-y-2">
            <div className="flex items-center">
              <input type="checkbox" id="torrefacao" className="h-4 w-4 text-green-500 rounded" checked />
              <label htmlFor="torrefacao" className="ml-2 text-sm text-gray-700">Torrefação</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="cafeteria" className="h-4 w-4 text-green-500 rounded" checked />
              <label htmlFor="cafeteria" className="ml-2 text-sm text-gray-700">Cafeteria</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="ecommerce" className="h-4 w-4 text-green-500 rounded" checked />
              <label htmlFor="ecommerce" className="ml-2 text-sm text-gray-700">E-commerce</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="delivery" className="h-4 w-4 text-green-500 rounded" />
              <label htmlFor="delivery" className="ml-2 text-sm text-gray-700">Delivery</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="livraria" className="h-4 w-4 text-green-500 rounded" />
              <label htmlFor="livraria" className="ml-2 text-sm text-gray-700">Livraria</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="coworking" className="h-4 w-4 text-green-500 rounded" />
              <label htmlFor="coworking" className="ml-2 text-sm text-gray-700">Coworking/Eventos</label>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="coffeeshop" className="h-4 w-4 text-green-500 rounded" />
              <label htmlFor="coffeeshop" className="ml-2 text-sm text-gray-700">Coffee Shop</label>
            </div>
          </div>
        </div>
        
        {/* Controle de Estoque */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h2 className="font-semibold mb-4">Controle de Estoque</h2>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estoque Atual</label>
              <div className="flex">
                <button className="bg-gray-100 px-3 py-2 rounded-l-lg flex items-center justify-center">
                  <Minus size={14} className="text-gray-600" />
                </button>
                <input 
                  type="text" 
                  value="20"
                  className="w-16 p-2 border-t border-b border-gray-200 text-center text-sm focus:outline-none"
                />
                <button className="bg-gray-100 px-3 py-2 rounded-r-lg flex items-center justify-center">
                  <Plus size={14} className="text-gray-600" />
                </button>
                <select className="ml-2 p-2 border border-gray-200 rounded-lg text-sm appearance-none bg-gray-100">
                  <option>kg</option>
                  <option>g</option>
                  <option>un</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estoque Mínimo</label>
              <div className="flex">
                <input 
                  type="text" 
                  value="5"
                  className="flex-1 p-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <select className="ml-2 p-2 border border-gray-200 rounded-lg text-sm appearance-none bg-gray-100">
                  <option>kg</option>
                  <option>g</option>
                  <option>un</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Alerta de Estoque</label>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">Desativado</span>
              <div className="relative w-10 h-6 bg-green-500 rounded-full">
                <div className="absolute w-4 h-4 bg-white rounded-full top-1 right-1"></div>
              </div>
              <span className="text-xs text-gray-500">Ativado</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Receba alertas quando o estoque estiver abaixo do mínimo</p>
          </div>
        </div>
        
        {/* Espaço para o botão */}
        <div className="h-16"></div>
      </div>

      {/* Botão de salvar */}
      <div className="p-4 bg-white border-t border-gray-200 shadow-lg fixed bottom-0 left-0 right-0">
        <button className="w-full p-3 bg-green-500 text-white font-medium rounded-lg flex items-center justify-center">
          <Save size={18} className="mr-2" />
          <span>Salvar Alterações</span>
        </button>
      </div>
    </div>
  );
};

export default ProductEditScreen;
