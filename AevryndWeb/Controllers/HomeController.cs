using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

public sealed class HomeController : Controller
{
    [HttpGet("/")]
    public IActionResult Index() => View();

    [HttpGet("/Home/Error")]
    public IActionResult Error() => Problem("網站暫時無法處理此要求。");
}
