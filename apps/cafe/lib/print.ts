import type { Order, OrderItem } from './types';
import { formatCurrency } from './utils/format';

/**
 * Generates receipt HTML for thermal printing
 */
export function generateReceiptHTML(order: Order): string {
  const bebidasItems = order.items.filter((i) => i.station === 'bebidas');
  const comidasItems = order.items.filter((i) => i.station === 'comidas');

  const formatDate = (date: Date) => {
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderItems = (items: OrderItem[]) => {
    return items
      .map(
        (item) => `
        <tr>
          <td style="text-align: left;">${item.quantity}x ${item.name}</td>
          <td style="text-align: right;">${formatCurrency(item.price * item.quantity)}</td>
        </tr>
        ${item.notes ? `<tr><td colspan="2" style="font-size: 10px; padding-left: 12px;">→ ${item.notes}</td></tr>` : ''}
      `
      )
      .join('');
  };

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        @page {
          size: 80mm auto;
          margin: 0;
        }
        body {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          line-height: 1.3;
          margin: 0;
          padding: 8px;
          width: 80mm;
        }
        .header {
          text-align: center;
          border-bottom: 1px dashed #000;
          padding-bottom: 8px;
          margin-bottom: 8px;
        }
        .title {
          font-size: 14px;
          font-weight: bold;
        }
        .section {
          margin-bottom: 8px;
        }
        .section-title {
          font-weight: bold;
          border-bottom: 1px solid #000;
          margin-bottom: 4px;
          padding-bottom: 2px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        td {
          padding: 2px 0;
        }
        .total {
          border-top: 1px dashed #000;
          margin-top: 8px;
          padding-top: 8px;
          font-weight: bold;
          font-size: 14px;
        }
        .footer {
          text-align: center;
          border-top: 1px dashed #000;
          margin-top: 12px;
          padding-top: 8px;
          font-size: 10px;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="title">CONSCIÊNCIA CAFÉ</div>
        <div>Foz do Iguaçu - PR</div>
      </div>

      <div>
        <strong>Cliente:</strong> ${order.customerName}<br>
        <strong>Atendente:</strong> ${order.baristaName}<br>
        <strong>Data:</strong> ${formatDate(order.createdAt)}
      </div>

      ${
        bebidasItems.length > 0
          ? `
        <div class="section">
          <div class="section-title">BEBIDAS</div>
          <table>${renderItems(bebidasItems)}</table>
        </div>
      `
          : ''
      }

      ${
        comidasItems.length > 0
          ? `
        <div class="section">
          <div class="section-title">COMIDAS</div>
          <table>${renderItems(comidasItems)}</table>
        </div>
      `
          : ''
      }

      <div class="total">
        <table>
          <tr>
            <td>TOTAL:</td>
            <td style="text-align: right;">${formatCurrency(order.total)}</td>
          </tr>
        </table>
      </div>

      <div class="footer">
        Obrigado pela preferência!<br>
        ☕ Consciência Café
      </div>
    </body>
    </html>
  `;
}

/**
 * Generates kitchen ticket HTML (for preparation station)
 */
export function generateKitchenTicketHTML(
  order: Order,
  station: 'bebidas' | 'comidas'
): string {
  const items = order.items.filter((i) => i.station === station);

  if (items.length === 0) return '';

  const stationName = station === 'bebidas' ? 'BEBIDAS' : 'COMIDAS';

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        @page {
          size: 80mm auto;
          margin: 0;
        }
        body {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          line-height: 1.4;
          margin: 0;
          padding: 8px;
          width: 80mm;
        }
        .header {
          text-align: center;
          font-size: 18px;
          font-weight: bold;
          border: 2px solid #000;
          padding: 4px;
          margin-bottom: 8px;
        }
        .customer {
          font-size: 16px;
          font-weight: bold;
          margin-bottom: 8px;
        }
        .item {
          padding: 4px 0;
          border-bottom: 1px dotted #000;
        }
        .item-name {
          font-weight: bold;
        }
        .item-qty {
          font-size: 18px;
          font-weight: bold;
        }
        .notes {
          font-size: 12px;
          padding-left: 12px;
        }
        .time {
          text-align: center;
          margin-top: 12px;
          font-size: 12px;
        }
      </style>
    </head>
    <body>
      <div class="header">${stationName}</div>

      <div class="customer">${order.customerName}</div>

      ${items
        .map(
          (item) => `
        <div class="item">
          <span class="item-qty">${item.quantity}x</span>
          <span class="item-name">${item.name}</span>
          ${item.notes ? `<div class="notes">→ ${item.notes}</div>` : ''}
        </div>
      `
        )
        .join('')}

      <div class="time">
        ${new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </body>
    </html>
  `;
}

/**
 * Print using Web Print API
 */
export function printHTML(html: string) {
  // Create a hidden iframe for printing
  const iframe = document.createElement('iframe');
  iframe.style.position = 'absolute';
  iframe.style.width = '0';
  iframe.style.height = '0';
  iframe.style.border = 'none';
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow?.document;
  if (!doc) {
    document.body.removeChild(iframe);
    return;
  }

  doc.open();
  doc.write(html);
  doc.close();

  // Wait for content to load then print
  iframe.onload = () => {
    iframe.contentWindow?.print();
    // Remove iframe after a delay to allow print dialog
    setTimeout(() => {
      document.body.removeChild(iframe);
    }, 1000);
  };
}

/**
 * Print order receipt
 */
export function printReceipt(order: Order) {
  const html = generateReceiptHTML(order);
  printHTML(html);
}

/**
 * Print kitchen tickets for both stations
 */
export function printKitchenTickets(order: Order) {
  const bebidasHTML = generateKitchenTicketHTML(order, 'bebidas');
  const comidasHTML = generateKitchenTicketHTML(order, 'comidas');

  if (bebidasHTML) {
    printHTML(bebidasHTML);
  }

  // Small delay between prints
  if (comidasHTML) {
    setTimeout(() => {
      printHTML(comidasHTML);
    }, 500);
  }
}
