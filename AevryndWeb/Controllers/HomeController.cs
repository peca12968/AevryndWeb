using AevryndWeb.Models;
using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;

namespace AevryndWeb.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        public IActionResult Index()
        {
            return View();
        }

        [HttpGet("/Showcase")]
        public IActionResult Showcase() => View();

        [Microsoft.AspNetCore.Authorization.Authorize(Policy = AevryndWeb.Security.PortalIdentity.PortalOwnerPolicy)]
        public IActionResult Portal() => View();

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
