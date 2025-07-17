import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")  # Твій токен бота в змінних середовища

# Глобальні змінні для гри
players = []
hands = {}
deck = []
discard_pile = []
current_turn = 0
flip_side = "light"  # "light" або "dark"
game_started = False

CARD_COLORS_LIGHT = ["red", "yellow", "green", "blue"]
CARD_COLORS_DARK = ["pink", "orange", "teal", "purple"]
VALUES_LIGHT = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "+2"]
VALUES_DARK = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "+5"]

SPECIAL_CARDS = [
    ("wild", "Flip"),
    ("wild", "Color"),
]

def build_deck():
    deck = []
    for color in CARD_COLORS_LIGHT:
        deck.append((color, "0", None, None))
        for val in VALUES_LIGHT[1:]:
            deck.append((color, val, None, None))
            deck.append((color, val, None, None))

    for color in CARD_COLORS_DARK:
        deck.append((None, None, color, "0"))
        for val in VALUES_DARK[1:]:
            deck.append((None, None, color, val))
            deck.append((None, None, color, val))

    for _ in range(4):
        deck.append(("wild", "Flip", "wild", "Flip"))
        deck.append(("wild", "Color", "wild", "Color"))

    random.shuffle(deck)
    return deck

def format_card(card, side):
    if side == "light":
        color, value, _, _ = card
    else:
        _, _, color, value = card

    if color is None:
        color = "wild"
    return f"{color} {value}"

def format_hand(hand, side):
    return "\n".join(f"{i+1}. {format_card(card, side)}" for i, card in enumerate(hand))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, hands, deck, discard_pile, current_turn, flip_side, game_started
    players = []
    hands = {}
    deck = []
    discard_pile = []
    current_turn = 0
    flip_side = "light"
    game_started = False

    await update.message.reply_text(
        "Вітаю! Це UNO Flip бот.\n"
        "Щоб приєднатись до гри, напиши /join\n"
        "Максимум 4 гравці."
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_started

    if game_started:
        await update.message.reply_text("Гра вже триває. Зачекай на наступну гру.")
        return

    user = update.effective_user
    if user.id in [p.id for p in players]:
        await update.message.reply_text("Ви вже в грі!")
        return

    if len(players) >= 4:
        await update.message.reply_text("Максимум 4 гравці, місць немає.")
        return

    players.append(user)
    await update.message.reply_text(f"{user.first_name} приєднався до гри! ({len(players)}/4)")

    if len(players) == 4:
        await start_game(update, context)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deck, hands, discard_pile, current_turn, game_started

    game_started = True
    deck = build_deck()
    hands.clear()

    for player in players:
        hands[player.id] = [deck.pop() for _ in range(7)]

    while True:
        top_card = deck.pop()
        if top_card[1] != "Flip" and top_card[3] != "Flip":
            discard_pile = [top_card]
            break
        else:
            deck.insert(0, top_card)

    current_turn = 0

    for player in players:
        await context.bot.send_message(
            chat_id=player.id,
            text=f"Гра почалась! Твоя рука:\n{format_hand(hands[player.id], flip_side)}",
        )

    await update.message.reply_text(
        f"Гра почалась! Перший ходить: {players[current_turn].first_name}\n"
        f"На столі карта: {format_card(discard_pile[-1], flip_side)}"
    )

    await prompt_player_turn(context)

async def prompt_player_turn(context: ContextTypes.DEFAULT_TYPE):
    global players, current_turn, hands, flip_side, discard_pile

    player = players[current_turn]
    keyboard = []

    hand = hands[player.id]
    buttons = [
        InlineKeyboardButton(
            text=f"Викинути {i+1}: {format_card(card, flip_side)}", callback_data=f"play_{i}"
        )
        for i, card in enumerate(hand)
    ]

    for i in range(0, len(buttons), 2):
        keyboard.append(buttons[i : i + 2])

    keyboard.append([InlineKeyboardButton("Добрати карту", callback_data="draw_card")])
    keyboard.append([InlineKeyboardButton("Сказати UNO", callback_data="say_uno")])
    keyboard.append([InlineKeyboardButton("Перевернути (Flip)", callback_data="flip_side")])

    await context.bot.send_message(
        chat_id=player.id,
        text=(
            f"Твій хід!\n"
            f"Карта на столі: {format_card(discard_pile[-1], flip_side)}\n"
            f"Твоя рука:\n{format_hand(hands[player.id], flip_side)}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

def next_turn():
    global current_turn, players
    current_turn = (current_turn + 1) % len(players)

def valid_play(card, top_card, side):
    color_card, value_card, color_card_dark, value_card_dark = card
    color_top, value_top, color_top_dark, value_top_dark = top_card

    if side == "light":
        if color_card == "wild":
            return True
        if color_card == color_top:
            return True
        if value_card == value_top:
            return True
    else:
        if color_card_dark == "wild":
            return True
        if color_card_dark == color_top_dark:
            return True
        if value_card_dark == value_top_dark:
            return True
    return False

async def process_play(update: Update, context: ContextTypes.DEFAULT_TYPE, player_id, card_index):
    global hands, discard_pile, current_turn, players, flip_side, deck, game_started

    if player_id != players[current_turn].id:
        await context.bot.send_message(chat_id=player_id, text="Зараз не твій хід!")
        return

    hand = hands[player_id]
    if card_index >= len(hand):
        await context.bot.send_message(chat_id=player_id, text="Невірний вибір карти!")
        return

    card = hand[card_index]
    top_card = discard_pile[-1]

    if not valid_play(card, top_card, flip_side):
        await context.bot.send_message(chat_id=player_id, text="Цю карту скинути не можна!")
        await prompt_player_turn(context)
        return

    discard_pile.append(card)
    hand.pop(card_index)

    if (flip_side == "light" and card[1] == "Flip") or (flip_side == "dark" and card[3] == "Flip"):
        flip_side = "dark" if flip_side == "light" else "light"
        await context.bot.send_message(
            chat_id=player_id,
            text=f"Flip! Тепер граємо на {flip_side} стороні."
        )

    if len(hand) == 0:
        for p in players:
            await context.bot.send_message(
                chat_id=p.id, text=f"Гравець {players[current_turn].first_name} виграв гру! 🎉"
            )
        game_started = False
        return

    next_turn()
    await prompt_player_turn(context)

async def process_draw(update: Update, context: ContextTypes.DEFAULT_TYPE, player_id):
    global deck, hands, current_turn, players, discard_pile

    if player_id != players[current_turn].id:
        await context.bot.send_message(chat_id=player_id, text="Зараз не твій хід!")
        return

    if len(deck) == 0:
        top = discard_pile.pop()
        deck.extend(discard_pile)
        random.shuffle(deck)
        discard_pile.clear()
        discard_pile.append(top)

    card = deck.pop()
    hands[player_id].append(card)
    await context.bot.send_message(
        chat_id=player_id,
        text=f"Ти добрав карту: {format_card(card, flip_side)}"
    )
    next_turn()
    await prompt_player_turn(context)

async def process_say_uno(update: Update, context: ContextTypes.DEFAULT_TYPE, player_id):
    if player_id != players[current_turn].id:
        await context.bot.send_message(chat_id=player_id, text="Зараз не твій хід!")
        return
    await context.bot.send_message(chat_id=player_id, text="Ти сказав UNO! Готуйся до закінчення гри!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if not game_started:
        await query.answer("Гра ще не почалась.")
        return

    if data.startswith("play_"):
        card_index = int(data.split("_")[1])
        await process_play(update, context, user_id, card_index)
        await query.answer()
    elif data == "draw_card":
        await process_draw(update, context, user_id)
        await query.answer()
    elif data == "say_uno":
        await process_say_uno(update, context, user_id)
        await query.answer()
    elif data == "flip_side":
        global flip_side
        flip_side = "dark" if flip_side == "light" else "light"
        await query.message.reply_text(f"Flip! Тепер граємо на {flip_side} стороні.")
        await query.answer()
        await prompt_player_turn(context)
    else:
        await query.answer("Невідома команда.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
