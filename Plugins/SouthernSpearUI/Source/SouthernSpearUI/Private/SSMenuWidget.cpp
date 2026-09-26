// Copyright Southern Spear. All Rights Reserved.

#include "SSMenuWidget.h"

#include "Components/ScaleBox.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SSUIAssets.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

const TCHAR* USSMenuWidget::FrontEndMap = TEXT("/Game/Maps/L_SS_FrontEnd");

namespace
{
	UWidget* KeyArt(UWidgetTree* T)
	{
		UImage* Art = T->ConstructWidget<UImage>();
		if (UTexture2D* Texture = SSUIAssets::KeyArt())
		{
			Art->SetBrushFromTexture(Texture, /*bMatchSize=*/ true);
		}
		else
		{
			Art->SetColorAndOpacity(SSPalette::Ink950());
		}
		UScaleBox* Scale = T->ConstructWidget<UScaleBox>();
		Scale->SetStretch(EStretch::ScaleToFill);
		Scale->AddChild(Art);
		return Scale;
	}
}

void USSMenuWidget::Setup(ESSMenuMode InMode)
{
	Mode = InMode;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	if (Mode == ESSMenuMode::FrontEnd)
	{
		Fill(Root, KeyArt(T));
		// Darken the left third so the menu reads over the art.
		UBorder* Shade = Plate(T, SSPalette::Ink950(0.72f), FMargin(0.f));
		UCanvasPanelSlot* ShadeSlot = Root->AddChildToCanvas(Shade);
		ShadeSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
		ShadeSlot->SetOffsets(FMargin(0.f, 0.f, 560.f, 0.f));
	}
	else
	{
		Fill(Root, Plate(T, SSPalette::Ink950(0.55f), FMargin(0.f)));
	}

	UVerticalBox* Column = T->ConstructWidget<UVerticalBox>();
	if (Mode == ESSMenuMode::FrontEnd)
	{
		Pin(Root, Column, FVector2D(0.f, 0.5f), FVector2D(72.f, 0.f));
	}
	else
	{
		Pin(Root, Column, FVector2D(0.5f, 0.5f), FVector2D(0.f, 0.f));
	}

	AddV(Column, Rule(T, SSPalette::Brass500(), 2.f, 96.f), 0.f, HAlign_Left);
	UTextBlock* Kicker = Text(T, 12, true, SSPalette::Brass300(), 300);
	Kicker->SetText(Mode == ESSMenuMode::FrontEnd
		? NSLOCTEXT("SSMenu", "Kicker", "PRE-ALPHA  ·  PHASE 1 VERTICAL SLICE")
		: NSLOCTEXT("SSMenu", "Paused", "MATCH MENU  ·  THE MATCH CONTINUES"));
	AddV(Column, Kicker, 14.f);
	UTextBlock* Title = Text(T, Mode == ESSMenuMode::FrontEnd ? 54 : 34, true, SSPalette::Sand100(), 120);
	Title->SetText(NSLOCTEXT("SSMenu", "Title", "SOUTHERN SPEAR"));
	AddV(Column, Title, 4.f);
	AddV(Column, Rule(T, SSPalette::Line(0.9f), 1.f, 420.f), 16.f, HAlign_Left);

	auto AddButton = [&](const FText& Label, FName Handler)
	{
		UButton* Button = MenuButton(T, Label);
		FScriptDelegate Delegate;
		Delegate.BindUFunction(this, Handler);
		Button->OnClicked.Add(Delegate);
		AddV(Column, Button, 10.f, HAlign_Left);
	};
	if (Mode == ESSMenuMode::FrontEnd)
	{
		UTextBlock* Mode1 = Text(T, 11, true, SSPalette::Sage400(), 200);
		Mode1->SetText(NSLOCTEXT("SSMenu", "Deploy", "DEPLOY  ·  OBJECTIVE ASSAULT  ·  WITH BOTS"));
		AddV(Column, Mode1, 18.f);
		AddButton(NSLOCTEXT("SSMenu", "RedGum", "RED GUM STATION"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRedGum));
		AddButton(NSLOCTEXT("SSMenu", "DryRiver", "DRY RIVER"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnDryRiver));
		AddV(Column, T->ConstructWidget<USpacer>(), 18.f);
		AddButton(NSLOCTEXT("SSMenu", "Quit", "QUIT TO DESKTOP"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit));

		UTextBlock* Footer = Text(T, 11, false, SSPalette::Sage400(), 80);
		Footer->SetText(NSLOCTEXT("SSMenu", "Footer", "A fictional setting. Not affiliated with any real defence force."));
		Pin(Root, Footer, FVector2D(0.f, 1.f), FVector2D(72.f, -32.f));
	}
	else
	{
		AddButton(NSLOCTEXT("SSMenu", "Resume", "RESUME"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnResume));
		AddButton(NSLOCTEXT("SSMenu", "MainMenu", "LEAVE MATCH"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnMainMenu));
		AddButton(NSLOCTEXT("SSMenu", "QuitGame", "QUIT TO DESKTOP"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit));
	}
}

void USSMenuWidget::PlayMap(const UObject* Context, const TCHAR* Map)
{
	UGameplayStatics::OpenLevel(Context, FName(Map), /*bAbsolute=*/ true, TEXT("NumBots=8"));
}

void USSMenuWidget::OnRedGum()   { PlayMap(this, TEXT("/Game/Maps/L_RedGum_01")); }
void USSMenuWidget::OnDryRiver() { PlayMap(this, TEXT("/Game/Maps/L_DryRiver_01")); }

void USSMenuWidget::OnResume()
{
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
	SetVisibility(ESlateVisibility::Collapsed);
}

void USSMenuWidget::OnMainMenu()
{
	UGameplayStatics::OpenLevel(this, FName(FrontEndMap), /*bAbsolute=*/ true);
}

void USSMenuWidget::OnQuit()
{
	UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
}
