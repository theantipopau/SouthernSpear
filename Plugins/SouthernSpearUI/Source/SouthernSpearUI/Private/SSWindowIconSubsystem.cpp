// Copyright Southern Spear. All Rights Reserved.

#include "SSWindowIconSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GenericPlatform/GenericWindow.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "UObject/UObjectGlobals.h"
#include "Widgets/SWindow.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#include <windows.h>
#include "Windows/HideWindowsPlatformTypes.h"
#endif

void USSWindowIconSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (!GIsEditor && !IsRunningCommandlet())
	{
		TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &USSWindowIconSubsystem::TryApply), 0.5f);
	}
}

void USSWindowIconSubsystem::Deinitialize()
{
	FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
	Super::Deinitialize();
}

bool USSWindowIconSubsystem::TryApply(float DeltaTime)
{
	Waited += DeltaTime;
	if (bApplied || Waited > 120.f)
	{
		return false; // done, or no game window after two minutes
	}
#if PLATFORM_WINDOWS
	if (!GEngine || !GEngine->GameViewport)
	{
		return true;
	}
	const TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow();
	const TSharedPtr<FGenericWindow> Native = Window.IsValid() ? Window->GetNativeWindow() : nullptr;
	HWND Handle = Native.IsValid() ? static_cast<HWND>(Native->GetOSWindowHandle()) : nullptr;
	FString Icon = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir() / TEXT("Build/Windows/Application.ico"));
	if (!IFileManager::Get().FileExists(*Icon)) // Build/ is not in git; the producer's icon is
	{
		Icon = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir() / TEXT("Docs/images/SouthernSpear.ico"));
	}
	if (!Handle)
	{
		return true; // window not created yet
	}
	if (!IFileManager::Get().FileExists(*Icon))
	{
		return false; // packaged: the exe already carries the icon
	}
	HICON Big = static_cast<HICON>(LoadImageW(nullptr, *Icon, IMAGE_ICON, GetSystemMetrics(SM_CXICON), GetSystemMetrics(SM_CYICON), LR_LOADFROMFILE));
	HICON Small = static_cast<HICON>(LoadImageW(nullptr, *Icon, IMAGE_ICON, GetSystemMetrics(SM_CXSMICON), GetSystemMetrics(SM_CYSMICON), LR_LOADFROMFILE));
	if (!Big || !Small)
	{
		UE_LOG(LogTemp, Warning, TEXT("SSWindowIcon could not load %s"), *Icon);
		return false;
	}
	// Window icons (title bar, Alt+Tab) and the class icons (the taskbar button falls back to these).
	SendMessageW(Handle, WM_SETICON, ICON_BIG, reinterpret_cast<LPARAM>(Big));
	SendMessageW(Handle, WM_SETICON, ICON_SMALL, reinterpret_cast<LPARAM>(Small));
	SetClassLongPtrW(Handle, GCLP_HICON, reinterpret_cast<LONG_PTR>(Big));
	SetClassLongPtrW(Handle, GCLP_HICONSM, reinterpret_cast<LONG_PTR>(Small));
	bApplied = true;
	const bool bSet = reinterpret_cast<HICON>(SendMessageW(Handle, WM_GETICON, ICON_BIG, 0)) == Big;
	UE_LOG(LogTemp, Log, TEXT("SSWindowIcon applied=%d from %s"), bSet, *Icon);
#endif
	return false;
}
