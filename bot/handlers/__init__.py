from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.oauth import router as oauth_router
from bot.handlers.upload import router as upload_router

router = Router()
router.include_router(start_router)
router.include_router(oauth_router)
router.include_router(upload_router)
