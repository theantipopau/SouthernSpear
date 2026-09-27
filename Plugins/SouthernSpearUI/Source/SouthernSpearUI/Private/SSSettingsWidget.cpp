// Copyright Southern Spear. All Rights Reserved.

#include "SSSettingsWidget.h"

#include "Components/BackgroundBlur.h"
#include "GameFramework/GameUserSettings.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SSUserPrefs.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	const int32 FrameLimits[] = { 30, 60, 120, 144, 0 };
	const EWindowMode::Type WindowModes[] = { EWindowMode::Fullscreen, EWindowMode::WindowedFullscreen, EWindowMode::Windowed };

	UGameUserSettings* Settings() { return GEngine ? GEngine->GetGameUserSettings() : nullptr; }

	UButton* ArrowButton(UWidgetTree* T, const TCHAR* Glyph)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		FButtonStyle Style = Button->GetStyle();
		auto Flat = [](const FLinearColor& C) { FSlateBrush B; B.DrawAs = ESlateBrushDrawType::Box; B.TintColor = FSlateColor(C); return B; };
		Style.SetNormal(Flat(SSPalette::Field700(0.9f)));
		Style.SetHovered(Flat(SSPalette::Brass500(0.95f)));
		Style.SetPressed(Flat(SSPalette::Brass300()));
		Style.SetNormalPadding(FMargin(10.f, 4.f));
		Style.SetPressedPadding(FMargin(10.f, 4.f));
		Button->SetStyle(Style);
		UTextBlock* Label = Text(T, 14, true, SSPalette::Sand100());
		Label->SetText(FText::FromString(Glyph));
		Button->AddChild(Label);
		return Button;
	}
}

void USSSettingRow::Step(int32 Delta)
{
	if (Options.Num() == 0)
	{
		return;
	}
	Index = (Index + Delta + Options.Num()) % Options.Num();
	Refresh();
	if (OnChanged)
	{
		OnChanged(Index);
	}
}

void USSSettingRow::Refresh()
{
	if (ValueText && Options.IsValidIndex(Index))
	{
		ValueText->SetText(Options[Index]);
	}
}

USSSettingRow* USSSettingsWidget::AddRow(UVerticalBox* Box, const FText& Label, TArray<FText> Options, int32 Current, TFunction<void(int32)> OnChanged)
{
	UWidgetTree* T = WidgetTree;
	USSSettingRow* Row = NewObject<USSSettingRow>(this);
	Row->Options = MoveTemp(Options);
	Row->Index = FMath::Clamp(Current, 0, FMath::Max(0, Row->Options.Num() - 1));
	Row->OnChanged = MoveTemp(OnChanged);

	UBorder* Plate1 = Plate(T, SSPalette::Field800(0.85f), FMargin(16.f, 8.f));
	UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
	Plate1->SetContent(Line);
	UTextBlock* Name = Text(T, 13, true, SSPalette::Sage200(), 160);
	Name->SetText(Label.ToUpper());
	AddH(Line, Name, true);

	UButton* Prev = ArrowButton(T, TEXT("‹"));
	FScriptDelegate PrevDelegate;
	PrevDelegate.BindUFunction(Row, GET_FUNCTION_NAME_CHECKED(USSSettingRow, Prev));
	Prev->OnClicked.Add(PrevDelegate);
	AddH(Line, Prev);

	USizeBox* ValueSize = T->ConstructWidget<USizeBox>();
	ValueSize->SetWidthOverride(200.f);
	Row->ValueText = Text(T, 14, true, SSPalette::Sand100(), 60);
	Row->ValueText->SetJustification(ETextJustify::Center);
	ValueSize->AddChild(Row->ValueText);
	AddH(Line, ValueSize);

	UButton* Next = ArrowButton(T, TEXT("›"));
	FScriptDelegate NextDelegate;
	NextDelegate.BindUFunction(Row, GET_FUNCTION_NAME_CHECKED(USSSettingRow, Next));
	Next->OnClicked.Add(NextDelegate);
	AddH(Line, Next);

	AddV(Box, Plate1, 4.f);
	Row->RowWidget = Plate1;
	Row->Refresh();
	Rows.Add(Row);
	Animated.Add(Plate1);
	return Row;
}

bool USSSettingsWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Blurred, darkened backdrop over whatever is behind (menu art or the match).
	UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
	Blur->SetBlurStrength(8.f);
	Fill(Root, Blur);
	Fill(Root, Plate(T, SSPalette::Ink950(0.55f), FMargin(0.f)));

	UVerticalBox* Frame = T->ConstructWidget<UVerticalBox>();
	Panel = Frame;
	Pin(Root, Frame, FVector2D(0.5f, 0.5f), FVector2D(0.f, 0.f));
	AddV(Frame, Rule(T, SSPalette::Brass500(), 2.f, 720.f));
	UBorder* Body = Plate(T, SSPalette::Ink900(0.94f), FMargin(28.f, 20.f, 28.f, 24.f));
	AddV(Frame, Body);
	USizeBox* Width = T->ConstructWidget<USizeBox>();
	Width->SetWidthOverride(664.f);
	Body->SetContent(Width);
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Width->AddChild(Col);

	UTextBlock* Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
	Kicker->SetText(NSLOCTEXT("SSSettings", "Kicker", "SOUTHERN SPEAR"));
	AddV(Col, Kicker);
	UTextBlock* Title = Text(T, 32, true, SSPalette::Sand100(), 100);
	Title->SetText(NSLOCTEXT("SSSettings", "Title", "SETTINGS"));
	AddV(Col, Title, 2.f);

	UGameUserSettings* S = Settings();

	UTextBlock* Display = Text(T, 11, true, SSPalette::Brass300(), 300);
	Display->SetText(NSLOCTEXT("SSSettings", "Display", "DISPLAY"));
	AddV(Col, Display, 18.f);

	const EWindowMode::Type Mode = S ? S->GetFullscreenMode() : EWindowMode::Windowed;
	int32 ModeIndex = 2;
	for (int32 I = 0; I < 3; ++I) { if (WindowModes[I] == Mode) { ModeIndex = I; } }
	AddRow(Col, NSLOCTEXT("SSSettings", "WindowMode", "Window mode"),
		{ NSLOCTEXT("SSSettings", "Fullscreen", "Fullscreen"), NSLOCTEXT("SSSettings", "Borderless", "Borderless"), NSLOCTEXT("SSSettings", "Windowed", "Windowed") },
		ModeIndex, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetFullscreenMode(WindowModes[I]); } });

	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Resolutions);
	if (Resolutions.Num() == 0)
	{
		Resolutions = { FIntPoint(1280, 720), FIntPoint(1600, 900), FIntPoint(1920, 1080), FIntPoint(2560, 1440) };
	}
	TArray<FText> ResText;
	int32 ResIndex = Resolutions.Num() - 1;
	const FIntPoint Current = S ? S->GetScreenResolution() : FIntPoint(1920, 1080);
	for (int32 I = 0; I < Resolutions.Num(); ++I)
	{
		ResText.Add(FText::FromString(FString::Printf(TEXT("%d × %d"), Resolutions[I].X, Resolutions[I].Y)));
		if (Resolutions[I] == Current) { ResIndex = I; }
	}
	TArray<FIntPoint> ResCopy = Resolutions;
	AddRow(Col, NSLOCTEXT("SSSettings", "Resolution", "Resolution"), ResText, ResIndex,
		[ResCopy](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetScreenResolution(ResCopy[I]); } });

	const int32 Quality = S ? FMath::Clamp(S->GetOverallScalabilityLevel(), 0, 3) : 2;
	AddRow(Col, NSLOCTEXT("SSSettings", "Quality", "Graphics quality"),
		{ NSLOCTEXT("SSSettings", "Low", "Low"), NSLOCTEXT("SSSettings", "Medium", "Medium"), NSLOCTEXT("SSSettings", "High", "High"), NSLOCTEXT("SSSettings", "Epic", "Epic") },
		Quality, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetOverallScalabilityLevel(I); } });

	AddRow(Col, NSLOCTEXT("SSSettings", "VSync", "Vertical sync"),
		{ NSLOCTEXT("SSSettings", "Off", "Off"), NSLOCTEXT("SSSettings", "On", "On") },
		S && S->IsVSyncEnabled() ? 1 : 0, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetVSyncEnabled(I == 1); } });

	int32 LimitIndex = 4;
	const float Limit = S ? S->GetFrameRateLimit() : 0.f;
	for (int32 I = 0; I < 5; ++I) { if (FMath::IsNearlyEqual(Limit, static_cast<float>(FrameLimits[I]))) { LimitIndex = I; } }
	AddRow(Col, NSLOCTEXT("SSSettings", "FrameLimit", "Frame rate limit"),
		{ FText::FromString(TEXT("30")), FText::FromString(TEXT("60")), FText::FromString(TEXT("120")), FText::FromString(TEXT("144")),
		  NSLOCTEXT("SSSettings", "Unlimited", "Unlimited") },
		LimitIndex, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetFrameRateLimit(static_cast<float>(FrameLimits[I])); } });

	UTextBlock* Gameplay = Text(T, 11, true, SSPalette::Brass300(), 300);
	Gameplay->SetText(NSLOCTEXT("SSSettings", "Gameplay", "VIEW"));
	AddV(Col, Gameplay, 18.f);
	TArray<FText> FovText;
	int32 FovIndex = 0;
	const int32 FovNow = FMath::RoundToInt(FSSUserPrefs::GetFieldOfView());
	for (int32 Fov = static_cast<int32>(FSSUserPrefs::MinFieldOfView), I = 0; Fov <= static_cast<int32>(FSSUserPrefs::MaxFieldOfView); Fov += 5, ++I)
	{
		FovText.Add(FText::FromString(FString::Printf(TEXT("%d°"), Fov)));
		if (Fov <= FovNow) { FovIndex = I; }
	}
	AddRow(Col, NSLOCTEXT("SSSettings", "Fov", "Field of view"), FovText, FovIndex,
		[](int32 I) { FSSUserPrefs::SetFieldOfView(FSSUserPrefs::MinFieldOfView + 5.f * I); });

	// Buttons.
	UHorizontalBox* Buttons = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, Buttons, 22.f, HAlign_Right);
	UButton* Back = MenuButton(T, NSLOCTEXT("SSSettings", "Back", "BACK"), 150.f);
	FScriptDelegate BackDelegate;
	BackDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnBack));
	Back->OnClicked.Add(BackDelegate);
	AddH(Buttons, Back)->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
	UButton* Apply = MenuButton(T, NSLOCTEXT("SSSettings", "Apply", "APPLY"), 150.f);
	FScriptDelegate ApplyDelegate;
	ApplyDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnApply));
	Apply->OnClicked.Add(ApplyDelegate);
	AddH(Buttons, Apply);
	Animated.Add(Buttons);
	return true;
}

void USSSettingsWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	Reveal(Panel, Ease(Elapsed, 0.f, 0.3f), 18.f, /*bVertical=*/ true);
	for (int32 Index = 0; Index < Animated.Num(); ++Index)
	{
		Reveal(Animated[Index], Ease(Elapsed, 0.08f + 0.04f * Index, 0.3f), 16.f);
	}
}

void USSSettingsWidget::OnApply()
{
	if (UGameUserSettings* S = Settings())
	{
		S->ApplySettings(/*bCheckForCommandLineOverrides=*/ false);
		S->SaveSettings();
	}
	OnBack();
}

void USSSettingsWidget::OnBack()
{
	SetVisibility(ESlateVisibility::Collapsed);
	if (OnClosed)
	{
		OnClosed();
	}
}
