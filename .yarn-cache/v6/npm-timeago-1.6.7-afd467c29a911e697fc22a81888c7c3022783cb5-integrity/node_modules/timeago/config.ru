use Rack::Static,
    urls: ["/test", "/locales"],
    root: "public"

run lambda { |_env|
  [
    200,
    {
      "Content-Type"  => "text/html",
      "Cache-Control" => "public, max-age=86400",
    },
    File.open("public/index.html", File::RDONLY),
  ]
}
