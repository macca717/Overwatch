# pylint: disable=unused-import

from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from loguru import logger
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .helpers import flash
from .models import metadata, reports
from .reports import ReportForm, ReportValidationError
from .settings import (
    BASE_DIR,
    DEBUG,
    ALLOWED_HOSTS,
    SECRET_KEY,
    DATABASE,
    DATABASE_URL,
    VIDEO_DIR,
    TEMPLATES,
)


async def home(request: Request):
    now = datetime.now()
    date_twelve_months_ago = now - timedelta(weeks=52)
    date_six_months_ago = now - timedelta(weeks=26)
    query = reports.select().where(reports.c.occurance_date > date_twelve_months_ago)
    last_year_results = await DATABASE.fetch_all(query)
    last_six_months_results = [
        x for x in last_year_results if x["occurance_date"] > date_six_months_ago
    ]
    last_year_count = len(last_year_results)
    try:
        average_length = mean([x["duration_minutes"] for x in last_year_results])
        longest = max([x["duration_minutes"] for x in last_year_results])
    except ValueError:
        longest = 0
        average_length = 0
    hospitalizations = sum([x["hospitalization_required"] for x in last_year_results])
    days_since_last_seizure = None
    seizure_dates = [x["occurance_date"] for x in last_year_results]
    if len(seizure_dates) > 0:
        last_date = max(seizure_dates)
        days_since_last_seizure = (now - last_date).days
    stats = dict(
        last_year_count=last_year_count,
        last_six_months_count=len(last_six_months_results),
        longest=longest,
        average_length=average_length,
        hospitalizations=hospitalizations,
        days_since_last_seizure=days_since_last_seizure,
    )
    return TEMPLATES.TemplateResponse(
        "index.html", {"request": request, "title": "Home", "context": stats}
    )


async def application(request: Request):
    return TEMPLATES.TemplateResponse("app.html", {"request": request, "title": "App"})


async def health(*_):
    """Health endpoint"""
    return Response(b"UP")


async def admin_landing(request: Request):
    return TEMPLATES.TemplateResponse(
        "admin/admin.html", {"request": request, "title": "Admin"}
    )


async def admin_dashboard(request: Request):
    return TEMPLATES.TemplateResponse(
        "admin/dashboard.html", {"request": request, "title": "Admin Dashboard"}
    )


async def admin_videos(request: Request):
    video_list = []
    entries = Path(VIDEO_DIR)
    for entry in entries.iterdir():
        if entry.is_file() and entry.match("*.avi"):
            video_list.append(entry.name)
    return TEMPLATES.TemplateResponse(
        "admin/videos.html",
        {"request": request, "title": "Videos", "ctx": {"videos": video_list}},
    )


async def admin_video_download(request: Request):
    file_name: str = request.path_params["video_file"]
    file_path = VIDEO_DIR / file_name
    if file_path.exists():
        return FileResponse(VIDEO_DIR / file_name)
    raise HTTPException(404)


async def seizure_reports(request: Request):
    if request.method == "POST":
        try:
            form = await request.form()
            data = ReportForm(form)
            query = reports.insert().values(**data.to_dict())
        except ReportValidationError as ex:
            logger.exception(ex)
            flash(request, str(ex))
            return RedirectResponse(
                request.url_for("add_seizure_report"), status_code=302
            )
        else:
            await DATABASE.execute(query)
            flash(request, "Event submitted", category="is-success")
            response = RedirectResponse(
                request.url_for("seizure_reports"), status_code=302
            )
            return response
    query = reports.select()
    results = await DATABASE.fetch_all(query)
    results.sort(key=lambda x: x["id"], reverse=True)
    return TEMPLATES.TemplateResponse(
        "reports/reports.html",
        {"request": request, "title": "Reports", "ctx": {"reports": results}},
    )


async def add_seizure_report(request: Request):
    return TEMPLATES.TemplateResponse(
        "reports/add_report.html",
        {"request": request, "title": "Add Report"},
    )


async def delete_seizure_report(request: Request):
    id_to_delete = request.path_params["id"]
    query = reports.delete().where(reports.c.id == id_to_delete)
    await DATABASE.execute(query)
    flash(request, "Deleted", "is-success")
    return RedirectResponse(request.url_for("seizure_reports"), status_code=302)


async def update_seizure_report(request: Request):
    try:
        form = await request.form()
        new_data = ReportForm(form)
    except ReportValidationError as ex:
        logger.exception(ex)
        flash(request, str(ex))
        return RedirectResponse(
            request.url_for("update_seizure_report"), status_code=302
        )
    else:
        query = (
            reports.update()
            .where(reports.c.id == form["id"])
            .values(**new_data.to_dict())
        )
        await DATABASE.execute(query)
        flash(request, "Updated", "is-success")
        return RedirectResponse(request.url_for("seizure_reports"), status_code=302)


async def seizure_report(request: Request):
    report_id = request.path_params["id"]
    query = reports.select().where(reports.c.id == report_id)
    result = await DATABASE.fetch_one(query)
    return TEMPLATES.TemplateResponse(
        "reports/report.html",
        {"request": request, "title": "Report", "ctx": {"report": result}},
    )


async def not_found(request: Request, ex: HTTPException):
    context = {
        "request": request,
        "title": "Not Found",
        "message": ex.detail,
    }
    return TEMPLATES.TemplateResponse(
        "404.html", context=context, status_code=ex.status_code
    )


async def server_error(request: Request, ex: HTTPException):
    context = {"request": request, "title": "Server Error", "message": ex.detail}
    return TEMPLATES.TemplateResponse(
        "500.html", context=context, status_code=ex.status_code
    )


routes = [
    Route("/", endpoint=home),
    Route("/health", endpoint=health),
    Route("/app", endpoint=application),
    Route("/add-report", endpoint=add_seizure_report),
    Mount(
        "/reports",
        routes=[
            Route("/", endpoint=seizure_reports, methods=["GET", "POST"]),
            Route("/{id:int}", endpoint=seizure_report),
            Route(
                "/delete/{id:int}",
                endpoint=delete_seizure_report,
            ),
            Route("/update", endpoint=update_seizure_report, methods=["POST"]),
        ],
    ),
    Mount(
        "/admin",
        routes=[
            Route("/", endpoint=admin_landing),
            Route("/dashboard", endpoint=admin_dashboard),
            Route("/videos", endpoint=admin_videos),
            Route("/videos/{video_file:str}", endpoint=admin_video_download),
        ],
    ),
    Mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static"),
]

exception_handlers = {404: not_found, 500: server_error}

middleware = [
    Middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
    ),
    Middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS),
]

app = Starlette(
    debug=DEBUG,
    routes=routes,
    exception_handlers=exception_handlers,  # type: ignore
    middleware=middleware,
    on_startup=[DATABASE.connect],
    on_shutdown=[DATABASE.disconnect],
)
